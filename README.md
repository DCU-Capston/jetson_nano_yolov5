# YOLOv5 for Jetson Nano

이 저장소는 Jetson Nano에서 실행하기 위해 최적화된 YOLOv5 버전입니다. 불필요한 파일을 제거하고 핵심 기능만 남겨두었습니다.

## 설치 방법

```bash
# 필요한 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 이미지에서 객체 감지

```bash
python detect.py --weights yolov5s.pt --source path/to/image.jpg
```

### 비디오에서 객체 감지

```bash
python detect.py --weights yolov5s.pt --source path/to/video.mp4
```

### 웹캠으로 객체 감지

```bash
python detect.py --weights yolov5s.pt --source 0
```

## Jetson Nano에서 최적의 성능을 위한 팁

1. 가벼운 모델 사용 (yolov5s.pt 또는 yolov5n.pt)
2. 이미지 크기 줄이기 (--img 320)
3. 필요한 경우 `--half` 플래그 사용 (FP16 반정밀도)
4. 최적화된 전력 설정 적용 (`jetson_optimize.py` 사용)
5. 낮은 신뢰도 임계값 사용 (--conf 0.25)

## 최적화된 실행 명령어

```bash
# 최적화된 설정으로 웹캠 실행
python detect.py --weights yolov5n.pt --img 320 --conf 0.25 --source 0 --half

# Jetson 전력 모드 최적화 후 실행
python jetson_optimize.py --power max --model n --download
python detect.py --weights yolov5n.pt --img 320 --conf 0.25 --source 0 --half
```

## 포함된 파일

-   detect.py: 객체 감지 실행 스크립트
-   export.py: 다른 형식으로 모델 변환
-   models/: 모델 아키텍처 및 가중치 파일
-   utils/: 유틸리티 함수들
-   data/: 데이터셋 구성 파일
