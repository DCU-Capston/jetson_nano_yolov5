import numpy as np
import torch
import yaml
from tqdm import tqdm

from utils.general import LOGGER, colorstr, emojis
from utils.metrics import fitness
from utils.torch_utils import de_parallel


def check_anchor_order(m):
    """Check anchor order against stride order for YOLOv5 Detect() module m, and correct if necessary."""
    a = m.anchor_grid.prod(-1).view(-1)  # anchor area
    da = a[-1] - a[0]  # delta a
    ds = m.stride[-1] - m.stride[0]  # delta s
    if da.sign() != ds.sign():  # same order
        LOGGER.info(f"{colorstr('autoanchor: ')}Reversing anchor order")
        m.anchors[:] = m.anchors.flip(0)
        m.anchor_grid[:] = m.anchor_grid.flip(0)


def check_anchors(dataset, model, thr=4.0, imgsz=640):
    """Check anchor fit to data, recompute if necessary."""
    prefix = colorstr("autoanchor: ")
    LOGGER.info(f"\n{prefix}Analyzing anchors... ", end="")
    m = de_parallel(model).model[-1]  # Detect()
    shapes = imgsz * dataset.shapes / dataset.shapes.max(1, keepdims=True)
    scale = np.random.uniform(0.9, 1.1, size=(shapes.shape[0], 1))  # augment scale
    wh = torch.tensor(np.concatenate([l[:, 3:5] * s for s, l in zip(shapes * scale, dataset.labels)])).float()  # wh

    def metric(k):  # compute metric
        r = wh[:, None] / k[None]
        x = torch.min(r, 1 / r).min(2)[0]  # ratio metric
        best = x.max(1)[0]  # best_x
        aat = (x > 1 / thr).float().sum(1).mean()  # anchors above threshold
        bpr = (best > 1 / thr).float().mean()  # best possible recall
        return bpr, aat

    anchors = m.anchor_grid.clone().cpu().view(-1, 2)  # current anchors
    bpr, aat = metric(anchors)
    LOGGER.info(f"anchors/target = {aat:.2f}, Best Possible Recall (BPR) = {bpr:.4f}", end="")
    if bpr < 0.98:  # threshold to recompute
        LOGGER.info(". Attempting to improve anchors, please wait...")
        na = m.anchor_grid.numel() // 2  # number of anchors
        try:
            anchors = kmean_anchors(dataset, n=na, img_size=imgsz, thr=thr, gen=1000, verbose=False)
        except Exception as e:
            LOGGER.info(f"{prefix}ERROR: {e}")
        new_bpr = metric(anchors)[0]
        if new_bpr > bpr:  # replace anchors
            anchors = torch.tensor(anchors, device=m.anchors.device).type_as(m.anchors)
            m.anchor_grid[:] = anchors.clone().view_as(m.anchor_grid)  # for inference
            m.anchors[:] = anchors.clone().view_as(m.anchors) / m.stride.to(m.anchors.device).view(-1, 1, 1)  # loss
            check_anchor_order(m)
            LOGGER.info(f"{prefix}New anchors saved to model. Update model *.yaml to use these anchors in the future.")
        else:
            LOGGER.info(f"{prefix}Original anchors better than new anchors. Proceeding with original anchors.")
    LOGGER.info("")  # newline


def kmean_anchors(dataset="./data/coco128.yaml", n=9, img_size=640, thr=4.0, gen=1000, verbose=True):
    """Creates kmeans-evolved anchors from training dataset

    Arguments:
        dataset: path to data.yaml, or a loaded dataset
        n: number of anchors
        img_size: image size used for training
        thr: anchor-label wh ratio threshold hyperparameter hyp['anchor_t'] used for training, default=4.0
        gen: generations to evolve anchors using genetic algorithm
        verbose: print all results

    Return:
        k: kmeans evolved anchors

    Usage:
        from utils.autoanchor import *; _ = kmean_anchors()
    """
    from scipy.cluster.vq import kmeans

    npr = np.random
    thr = 1 / thr

    def metric(k, wh):  # compute metrics
        r = wh[:, None] / k[None]
        x = torch.min(r, 1 / r).min(2)[0]  # ratio metric
        # x = wh_iou(wh, torch.tensor(k))  # iou metric
        return x, x.max(1)[0]  # x, best_x

    def anchor_fitness(k):  # mutation fitness
        _, best = metric(torch.tensor(k, dtype=torch.float32), wh)
        return (best * (best > thr).float()).mean()  # fitness

    def print_results(k, verbose=True):
        k = k[np.argsort(k.prod(1))]  # sort small to large
        x, best = metric(k, wh0)
        bpr, aat = (best > thr).float().mean(), (x > thr).float().mean() * n  # best possible recall, anch > thr
        s = f"{prefix}thr={thr:.2f}: {bpr:.4f} best possible recall, {aat:.2f} anchors past thr\n" \
            f"{prefix}n={n}, img_size={img_size}, metric_all={x.mean():.3f}/{best.mean():.3f}-mean/best, " \
            f"past_thr={x[x > thr].mean():.3f}-mean: "
        for i, x in enumerate(k):
            s += "%i,%i, " % (round(x[0]), round(x[1]))
        if verbose:
            LOGGER.info(s[:-2])
        return k

    if isinstance(dataset, str):  # *.yaml file
        with open(dataset, errors="ignore") as f:
            data_dict = yaml.safe_load(f)  # model dict
        from utils.dataloaders import LoadImagesAndLabels

        dataset = LoadImagesAndLabels(data_dict["train"], augment=True, rect=True)

    # Get label wh
    shapes = img_size * dataset.shapes / dataset.shapes.max(1, keepdims=True)
    wh0 = np.concatenate([l[:, 3:5] * s for s, l in zip(shapes, dataset.labels)])  # wh

    # Filter
    i = (wh0 < 3.0).any(1).sum()
    if i:
        LOGGER.info(f"{prefix}WARNING: Extremely small objects found: {i} of {len(wh0)} labels are < 3 pixels in size")
    wh = wh0[(wh0 >= 2.0).any(1)]  # filter > 2 pixels
    # wh = wh * (npr.random(wh.shape) * 0.9 + 0.1)  # multiply by random scale 0-1

    # Kmeans calculation
    LOGGER.info(f"{prefix}Running kmeans for {n} anchors on {len(wh)} points...")
    s = wh.std(0)  # sigmas for whitening
    k, dist = kmeans(wh / s, n, iter=30)  # points, mean distance
    assert len(k) == n, f"{prefix}ERROR: scipy.cluster.vq.kmeans requested {n} points but returned only {len(k)}"
    k *= s
    wh = torch.tensor(wh, dtype=torch.float32)  # filtered
    wh0 = torch.tensor(wh0, dtype=torch.float32)  # unfiltered
    k = print_results(k, verbose=False)

    # Evolve
    npr = np.random
    f, sh, mp, s = anchor_fitness(k), k.shape, 0.9, 0.1  # fitness, generations, mutation prob, sigma
    pbar = tqdm(range(gen), desc=f"{prefix}Evolving anchors with Genetic Algorithm:")  # progress bar
    for _ in pbar:
        v = np.ones(sh)
        while (v == 1).all():  # mutate until a change occurs (prevent duplicates)
            v = ((npr.random(sh) < mp) * random.random() * npr.randn(*sh) * s + 1).clip(0.3, 3.0)
        kg = (k.copy() * v).clip(min=2.0)
        fg = anchor_fitness(kg)
        if fg > f:
            f, k = fg, kg.copy()
            pbar.desc = f"{prefix}Evolving anchors with Genetic Algorithm: fitness = {f:.4f}"
            if verbose:
                print_results(k, verbose)

    return print_results(k) 