#!/usr/bin/env python3
# YOLOv5 객체 감지 및 아두이노 LED 제어 프로그램
# 객체 감지 여부에 따라 LED 색상 제어: 감지 없음 - 초록색, 감지됨 - 빨간색

import argparse
import os
import sys
from pathlib import Path
import time

import torch
import cv2

# 필요한 경로 설정
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

# YOLOv5 모듈 가져오기
from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (
    LOGGER,
    check_file,
    check_img_size,
    check_imshow,
    check_requirements,
    increment_path,
    non_max_suppression,
    print_args,
    scale_boxes,
)
from utils.plots import Annotator, colors
from utils.torch_utils import select_device, smart_inference_mode

# 아두이노 제어 모듈 임포트
try:
    from arduino_control import ArduinoController
except ImportError:
    LOGGER.info("아두이노 제어 모듈을 찾을 수 없습니다. arduino_control.py 파일이 경로에 있는지 확인하세요.")
    ArduinoController = None

# 모델 캐싱 변수
MODEL_CACHE = {}

@smart_inference_mode()
def run(
    weights=ROOT / "yolov5s.pt",  # model path or triton URL
    source=ROOT / "data/images",  # file/dir/URL/glob/screen/0(webcam)
    data=ROOT / "data/coco128.yaml",  # dataset.yaml path
    imgsz=(640, 640),  # inference size (height, width)
    conf_thres=0.25,  # confidence threshold
    iou_thres=0.45,  # NMS IOU threshold
    max_det=1000,  # maximum detections per image
    device="",  # cuda device, i.e. 0 or 0,1,2,3 or cpu
    view_img=False,  # show results
    nosave=False,  # do not save images/videos
    classes=[0, 2, 5, 7],  # 사람(0), 자동차(2), 버스(5), 트럭(7)만 필터링
    agnostic_nms=False,  # class-agnostic NMS
    augment=False,  # augmented inference
    visualize=False,  # visualize features
    update=False,  # update all models
    project=ROOT / "runs/detect",  # save results to project/name
    name="exp",  # save results to project/name
    exist_ok=False,  # existing project/name ok, do not increment
    line_thickness=3,  # bounding box thickness (pixels)
    hide_labels=False,  # hide labels
    hide_conf=False,  # hide confidences
    half=False,  # use FP16 half-precision inference
    dnn=False,  # use OpenCV DNN for ONNX inference
    vid_stride=1,  # video frame-rate stride
    arduino_port='/dev/ttyACM0',  # 아두이노 시리얼 포트
    use_arduino=False,  # 아두이노 LED 제어 사용 여부
    target_classes=None,  # LED 상태를 변경할 대상 클래스(들)
    resolution=(1280, 720),  # 카메라 해상도 (너비, 높이)
    use_cached_model=True,  # 모델 캐싱 사용 여부
):
    """
    YOLOv5 객체 감지 및 아두이노 LED 제어를 실행합니다.
    
    객체 감지 여부에 따라 LED 색상을 제어합니다:
    - 객체가 감지되지 않으면 초록색 LED
    - 객체가 감지되면 빨간색 LED
    
    감지 대상: 사람(0), 자동차(2), 버스(5), 트럭(7)
    """
    global MODEL_CACHE
    
    source = str(source)
    save_img = not nosave and not source.endswith(".txt")  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(("rtsp://", "rtmp://", "http://", "https://"))
    webcam = source.isnumeric() or source.endswith(".streams") or (is_url and not is_file)
    screenshot = source.lower().startswith("screen")
    if is_url and is_file:
        source = check_file(source)  # download

    # 아두이노 컨트롤러 초기화
    arduino = None
    if use_arduino and ArduinoController is not None:
        try:
            arduino = ArduinoController(port=arduino_port)
            if not arduino.connected:
                LOGGER.warning(f"아두이노 연결 실패. LED 제어 기능이 비활성화됩니다.")
                arduino = None
            else:
                LOGGER.info(f"아두이노 연결 성공: {arduino_port}")
                # 초기 상태는 초록색 (감지 없음)
                arduino.set_green()
        except Exception as e:
            LOGGER.warning(f"아두이노 초기화 실패: {e}")
            arduino = None

    # 대상 클래스 설정
    if target_classes is None:
        # 기본값: 사람(0), 자동차(2), 버스(5), 트럭(7) 감지
        target_classes = [0, 2, 5, 7]

    # 디렉토리 설정
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # 모델 로드
    start_time = time.time()
    device = select_device(device)
    
    # 모델 캐싱 사용 시, 이전에 로드된 모델이 있으면 재사용
    cache_key = f"{weights}_{device}_{half}_{dnn}"
    if use_cached_model and cache_key in MODEL_CACHE:
        model = MODEL_CACHE[cache_key]
        print(f"캐시된 모델을 사용합니다. (로드 시간 절약)")
    else:
        model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
        if use_cached_model:
            MODEL_CACHE[cache_key] = model
            print(f"모델을 로드했습니다. ({time.time() - start_time:.2f}초)")
    
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # 데이터 로더
    bs = 1  # batch_size
    if webcam:
        view_img = check_imshow(warn=True)
        # 웹캠 설정 - 해상도 설정 추가
        cap = cv2.VideoCapture(int(source) if source.isnumeric() else source)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            cap.release()
        
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = len(dataset)
    elif screenshot:
        dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    vid_path, vid_writer = [None] * bs, [None] * bs

    # 추론 실행
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], [0.0, 0.0, 0.0]
    for path, im, im0s, vid_cap, s in dataset:
        # 이미지 전처리
        im = torch.from_numpy(im).to(model.device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        if webcam:
            im0s = im0s[0]  # 첫 번째 웹캠 프레임만 사용

        # 추론
        visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
        pred = model(im, augment=augment, visualize=visualize)

        # NMS
        # 사람(0), 자동차(2), 버스(5), 트럭(7)만 감지
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # 예측 처리
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s.copy(), dataset.count
                s += f"{i}: "
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, "frame", 0)

            p = Path(p)  # to Path
            s += "%gx%g " % im.shape[2:]  # print string
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            
            # 감지된 객체 수 초기화
            target_count = 0
            
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                    
                    # 대상 클래스에 속하는 객체 수 계산
                    # target_classes에 해당 클래스가 포함되어 있어도 확인 (항상 포함되어 있어야 함)
                    if int(c) in target_classes:
                        target_count += int(n)

                # 아두이노 LED 제어
                if arduino is not None:
                    if target_count == 0:
                        # 감지된 객체 없음 - 초록색
                        arduino.set_green()
                    else:
                        # 객체가 감지됨 - 빨간색
                        arduino.set_red()
                
                # 화면에 감지 정보 추가
                cv2.putText(
                    im0, 
                    f"사람/차량: {target_count}", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 0) if target_count == 0 else (0, 0, 255),  # 감지 없음: 초록색, 감지됨: 빨간색
                    2
                )
                
                # 해상도 정보 추가
                cv2.putText(
                    im0,
                    f"해상도: {im0.shape[1]}x{im0.shape[0]}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    1
                )

                # 검출 결과 그리기
                for *xyxy, conf, cls in reversed(det):
                    # 화면에 경계 상자 표시
                    if view_img:
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f"{names[c]} {conf:.2f}")
                        annotator.box_label(xyxy, label, color=colors(c, True))

            # 결과 표시
            im0 = annotator.result()
            if view_img:
                if not webcam:  # 이미지 파일인 경우
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond
                else:  # 웹캠인 경우
                    cv2.imshow('YOLOv5 Detection', im0)
                    if cv2.waitKey(1) == ord('q'):  # q를 누르면 종료
                        break

            # 결과 저장 (이미지/비디오)
            if save_img:
                if dataset.mode == "image":
                    cv2.imwrite(str(save_dir / p.name), im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_dir / p.name:  # new video
                        vid_path[i] = save_dir / p.name
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        vid_writer[i] = cv2.VideoWriter(
                            str(save_dir / f"{p.stem}.mp4"), 
                            cv2.VideoWriter_fourcc(*"mp4v"), 
                            fps, 
                            (w, h)
                        )
                    vid_writer[i].write(im0)

        # 결과 출력
        LOGGER.info(f"{s}Done.")

    # 마무리
    if arduino is not None:
        arduino.disconnect()


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default=ROOT / 'yolov5s.pt', help='모델 가중치 경로')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='파일/디렉토리/URL/glob/화면/0(웹캠)')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='데이터셋 YAML 파일 경로')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='추론 이미지 크기 [높이, 너비]')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='신뢰도 임계값')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU 임계값')
    parser.add_argument('--max-det', type=int, default=1000, help='이미지당 최대 검출 수')
    parser.add_argument('--device', default='', help='cuda 장치, 예: 0 또는 0,1,2,3 또는 cpu')
    parser.add_argument('--view-img', action='store_true', help='결과 표시')
    parser.add_argument('--nosave', action='store_true', help='이미지/비디오 저장하지 않음')
    parser.add_argument('--classes', nargs='+', type=int, default=[0, 2, 5, 7], help='특정 클래스만 필터링 (기본: 사람, 차량)')
    parser.add_argument('--agnostic-nms', action='store_true', help='클래스 구분 없는 NMS')
    parser.add_argument('--augment', action='store_true', help='확장된 추론')
    parser.add_argument('--visualize', action='store_true', help='특징 시각화')
    parser.add_argument('--update', action='store_true', help='모든 모델 업데이트')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='결과 저장 디렉토리')
    parser.add_argument('--name', default='exp', help='결과 저장 디렉토리 이름')
    parser.add_argument('--exist-ok', action='store_true', help='기존 디렉토리 덮어쓰기')
    parser.add_argument('--line-thickness', default=3, type=int, help='경계 상자 두께 (픽셀 단위)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='라벨 숨기기')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='신뢰도 숨기기')
    parser.add_argument('--half', action='store_true', help='FP16 반정밀도 추론 사용')
    parser.add_argument('--dnn', action='store_true', help='ONNX 추론을 위해 OpenCV DNN 사용')
    parser.add_argument('--vid-stride', type=int, default=1, help='비디오 프레임 레이트 간격')
    
    # 아두이노 LED 제어 관련 인자
    parser.add_argument('--arduino-port', type=str, default='/dev/ttyACM0', help='아두이노 시리얼 포트')
    parser.add_argument('--use-arduino', action='store_true', help='아두이노 LED 제어 사용')
    parser.add_argument('--target-classes', nargs='+', type=int, default=[0, 2, 5, 7], help='LED 상태를 변경할 대상 클래스(들) (기본: 사람, 차량)')
    
    # 카메라 해상도 설정
    parser.add_argument('--resolution', nargs='+', type=int, default=[1280, 720], help='카메라 해상도 [너비, 높이] (기본: 1280x720)')
    
    # 모델 캐싱 옵션
    parser.add_argument('--no-cache', action='store_true', help='모델 캐싱을 사용하지 않음 (기본: 사용)')
    
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    
    # 해상도 처리
    if len(opt.resolution) == 2:
        opt.resolution = tuple(opt.resolution)
    else:
        opt.resolution = (1280, 720)  # 기본값
    
    # 모델 캐싱 옵션 처리
    opt.use_cached_model = not opt.no_cache
    
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
