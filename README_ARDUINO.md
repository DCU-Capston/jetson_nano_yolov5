# YOLOv5 객체 감지와 아두이노 LED 경고 시스템

## 개요

이 프로젝트는 YOLOv5 객체 감지 시스템과 아두이노를 통합하여 객체 감지 상태에 따라 LED 색상을 변경하는 시스템입니다. Jetson Nano에서 YOLOv5를 사용하여 객체를 감지하고, 감지 결과에 따라 아두이노를 통해 연결된 LED의 색상을 제어합니다.

-   객체 감지 없음: 초록색 LED
-   객체 감지됨 (임계값 이상): 주황색 LED
-   여러 객체 감지됨 (위험 임계값 이상): 빨간색 LED

## 하드웨어 요구사항

-   Jetson Nano
-   아두이노 (예: Arduino Uno, Nano 등)
-   RGB LED (공통 양극/음극 타입)
-   저항 (LED 전류 제한용, 각 RGB 핀에 220-330Ω 저항 추천)
-   연결 케이블

## 하드웨어 연결 방법

1. 아두이노와 Jetson Nano를 USB 케이블로 연결합니다.
2. RGB LED를 아두이노에 다음과 같이 연결합니다:

    - RGB LED 빨간색 핀 -> 220-330Ω 저항 -> 아두이노 디지털 핀 9
    - RGB LED 초록색 핀 -> 220-330Ω 저항 -> 아두이노 디지털 핀 10
    - RGB LED 파란색 핀 -> 220-330Ω 저항 -> 아두이노 디지털 핀 11
    - RGB LED 공통 핀 -> 아두이노 GND (공통 음극 LED 사용 시) 또는 5V (공통 양극 LED 사용 시)

    **참고**: 공통 양극 LED를 사용하는 경우 arduino_led_control/led_control.ino 파일에서 LED 제어 함수를 수정해야 합니다.

## 소프트웨어 설치

### 1. 필요한 패키지 설치

```bash
pip install pyserial
```

### 2. 아두이노 코드 업로드

1. Arduino IDE를 설치합니다.
2. arduino_led_control/led_control.ino 파일을 Arduino IDE에서 엽니다.
3. 필요한 경우 RGB LED 핀 번호나 LED 타입에 맞게 코드를 수정합니다.
4. 아두이노에 코드를 업로드합니다.

## 사용 방법

### 기본 실행

웹캠으로부터 영상을 캡처하여 객체를 감지하고, 감지 결과에 따라 LED 색상을 제어합니다:

```bash
python detect.py --source 0 --use-arduino --arduino-port /dev/ttyACM0
```

### 고급 설정

다양한 매개변수를 사용하여 시스템 동작을 조정할 수 있습니다:

```bash
python detect.py --source 0 --use-arduino --arduino-port /dev/ttyACM0 --detection-threshold 2 --warning-threshold 5 --target-classes 0 2
```

### 매개변수 설명

-   `--use-arduino`: 아두이노 LED 제어 활성화
-   `--arduino-port`: 아두이노 시리얼 포트 (기본값: `/dev/ttyACM0`)
-   `--detection-threshold`: 주황색 LED로 변경할 객체 감지 임계값 (기본값: 1)
-   `--warning-threshold`: 빨간색 LED로 변경할 객체 감지 임계값 (기본값: 3)
-   `--target-classes`: LED 상태 변경을 위해 감지할 대상 클래스 (기본값: 사람(0), 자동차(2), 버스(5), 트럭(7))

## 문제 해결

### 아두이노 연결 문제

-   아두이노 포트 확인: `ls /dev/tty*` 명령을 실행하여 아두이노가 연결된 포트를 확인합니다.
-   권한 문제: `sudo chmod a+rw /dev/ttyACM0`와 같이 포트에 대한 읽기/쓰기 권한을 부여합니다.

### LED 동작 문제

-   LED 타입 확인: 공통 양극 LED를 사용하는 경우 아두이노 코드의 LED 제어 함수를 수정해야 합니다.
-   핀 번호 확인: LED가 아두이노의 올바른 핀에 연결되어 있는지 확인합니다.

## 라이센스

이 프로젝트는 YOLOv5와 동일한 라이센스(AGPL-3.0)를 따릅니다.

## 참고 자료

-   YOLOv5: https://github.com/ultralytics/yolov5
-   Arduino: https://www.arduino.cc/
