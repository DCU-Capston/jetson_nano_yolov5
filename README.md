# YOLOv5 객체 감지와 아두이노 LED 제어

이 프로젝트는 YOLOv5를 사용한 객체 감지와 아두이노 LED 제어 시스템입니다. 객체 감지 상태에 따라 LED 색상을 변경합니다:

-   객체가 감지되지 않으면 초록색 LED
-   객체가 감지되면 빨간색 LED (깜박임 효과)

**감지 대상**: 사람(0), 자동차(2), 버스(5), 트럭(7)만 감지합니다.

## 필요 조건

### 1. 하드웨어

-   컴퓨터 (Jetson Nano 권장)
-   웹캠
-   아두이노 (Arduino Uno/Nano 등)
-   WS2812B LED 스트립 (8x8 또는 유사한 형태)

### 2. 소프트웨어

-   Python 3.6+
-   PyTorch
-   OpenCV
-   pyserial
-   Arduino IDE

## 설치 방법

```bash
# 필요한 패키지 설치
pip3 install -r requirements.txt

# 아두이노 시리얼 포트 권한 설정 (Linux/macOS)
sudo usermod -a -G dialout $USER
```

## 사용 방법

### 1. 아두이노 설정

1. Arduino IDE를 사용하여 `arduino_led_control/led_control.ino` 파일을 아두이노에 업로드합니다.
2. WS2812B LED 스트립을 아두이노의 6번 핀에 연결합니다.

### 2. 객체 감지 및 LED 제어 실행

```bash
# 웹캠으로 객체 감지 및 아두이노 LED 제어 (기본 포트 /dev/ttyACM0)
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino

# 다른 아두이노 포트 지정
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino --arduino-port /dev/ttyUSB0

# macOS의 경우 (포트 예시)
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino --arduino-port /dev/cu.usbmodem14201
```

### 3. 감지 옵션 조정

이 프로젝트는 기본적으로 사람과 차량(자동차, 버스, 트럭)만 감지하도록 설정되어 있습니다. 다른 클래스를 감지하거나 특정 클래스만 감지하도록 하려면 다음과 같이 `--classes` 옵션을 사용하세요:

```bash
# 사람만 감지 (클래스 0)
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino --classes 0

# 자동차만 감지 (클래스 2)
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino --classes 2

# 모든 클래스 감지 (COCO 데이터셋의 80개 클래스)
python3 detect.py --weights yolov5s.pt --source 0 --use-arduino --classes
```

## 성능 최적화 팁

1. 가벼운 모델 사용 (yolov5s.pt 또는 yolov5n.pt)
2. 이미지 크기 줄이기 (--img 320)
3. 필요한 경우 `--half` 플래그 사용 (FP16 반정밀도)
4. 낮은 신뢰도 임계값 사용 (--conf 0.25)

```bash
# 최적화된 설정으로 웹캠 실행
python3 detect.py --weights yolov5n.pt --img 320 --conf 0.25 --source 0 --half --use-arduino
```

## 자주 묻는 질문

### 아두이노를 찾을 수 없다는 오류가 발생합니다.

-   아두이노가 컴퓨터에 연결되어 있는지 확인합니다.
-   올바른 포트를 지정했는지 확인합니다.
    -   Linux: `ls /dev/ttyACM*` 또는 `ls /dev/ttyUSB*`
    -   macOS: `ls /dev/cu.usbmodem*`
    -   Windows: 장치 관리자에서 COM 포트 확인
-   Linux/macOS에서 시리얼 포트 권한이 있는지 확인합니다. (`sudo usermod -a -G dialout $USER` 실행 후 재로그인)

### LED가 작동하지 않습니다.

-   아두이노 코드가 성공적으로 업로드되었는지 확인합니다.
-   LED 스트립이 올바르게 연결되었는지 확인합니다 (데이터 핀은 아두이노의 6번 핀에 연결).
-   LED 스트립에 충분한 전원이 공급되는지 확인합니다.

### 특정 객체가 감지되지 않습니다.

-   기본적으로 사람(0), 자동차(2), 버스(5), 트럭(7)만 감지하도록 설정되어 있습니다.
-   다른 객체를 감지하려면 `--classes` 옵션을 사용하여 원하는 클래스 ID를 지정하세요.
-   COCO 데이터셋의 클래스 ID 목록은 [여기](https://github.com/ultralytics/yolov5/blob/master/data/coco.yaml)에서 확인할 수 있습니다.

## 프로젝트 구조

-   `detect.py`: 객체 감지 및 아두이노 제어 스크립트
-   `arduino_control.py`: 아두이노 통신을 위한 Python 클래스
-   `arduino_led_control/led_control.ino`: 아두이노 LED 제어 코드
-   `models/`: YOLOv5 모델 파일
-   `utils/`: 유틸리티 함수들
-   `data/`: 데이터셋 구성 파일
