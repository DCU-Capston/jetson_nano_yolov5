# YOLOv5 객체 감지와 아두이노 LED 경고 시스템

## 개요

이 프로젝트는 YOLOv5 객체 감지 시스템과 아두이노를 통합하여 객체 감지 상태에 따라 LED 색상을 변경하는 시스템입니다. Jetson Nano에서 YOLOv5를 사용하여 객체를 감지하고, 감지 결과에 따라 아두이노를 통해 연결된 LED의 색상을 제어합니다.

-   객체 감지 없음: 초록색 LED
-   객체 감지됨 (임계값 이상): 주황색 LED
-   여러 객체 감지됨 (위험 임계값 이상): 빨간색 LED

## 하드웨어 요구사항

-   Jetson Nano
-   아두이노 (예: Arduino Uno, Nano 등)
-   WS2812B-64 LED 스트립
-   연결 케이블
-   5V 전원 공급 장치 (WS2812B LED 스트립용)

## 하드웨어 연결 방법

1. 아두이노와 Jetson Nano를 USB 케이블로 연결합니다.
2. WS2812B-64 LED 스트립을 아두이노에 다음과 같이 연결합니다:

    - WS2812B LED 데이터 핀 -> 아두이노 디지털 핀 6
    - WS2812B LED VCC -> 5V 전원 공급 장치 (+)
    - WS2812B LED GND -> 아두이노 GND 및 5V 전원 공급 장치 GND (-)

    **참고**:

    - 전류 요구사항: WS2812B LED는 전체 밝기에서 LED당 최대 60mA를 소비할 수 있습니다. 64개 LED의 경우 최대 64 \* 60mA = 3.84A가 필요할 수 있으므로 충분한 용량의 전원 공급 장치가 필요합니다.
    - 데이터 핀 보호: 아두이노의 데이터 핀과 WS2812B 데이터 핀 사이에 300-500Ω 저항을 추가하는 것이 권장됩니다.
    - 노이즈 감소: VCC와 GND 사이에 100-1000μF 커패시터를 추가하는 것이 좋습니다.

## 소프트웨어 설치

### 1. 필요한 패키지 설치 (Jetson Nano)

```bash
pip install pyserial
```

### 2. 아두이노 라이브러리 설치

1. Arduino IDE를 설치합니다.
2. Arduino IDE를 열고 메뉴에서 `스케치 > 라이브러리 포함하기 > 라이브러리 관리` 선택
3. 검색 창에 "Adafruit NeoPixel"을 입력하고 표시되는 라이브러리를 설치합니다.

### 3. 아두이노 코드 업로드

1. arduino_led_control/led_control.ino 파일을 Arduino IDE에서 엽니다.
2. 필요한 경우 다음 설정을 변경합니다:
    - `LED_PIN`: WS2812B LED 데이터 핀 (기본값: 6)
    - `LED_COUNT`: LED 개수 (기본값: 64)
    - `strip.setBrightness(50)`: LED 밝기 (0-255 범위, 기본값: 50)
3. 아두이노에 코드를 업로드합니다.

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

### WS2812B LED 문제

-   라이브러리 오류: Arduino IDE에서 "Adafruit NeoPixel" 라이브러리가 제대로 설치되었는지 확인합니다.
-   전원 문제: LED가 불규칙하게 깜박이거나 작동하지 않는 경우 충분한 전류를 공급하고 있는지 확인합니다.
-   데이터 신호 문제: 데이터 선이 올바른 핀에 연결되어 있고 필요한 경우 300-500Ω 저항을 사용하고 있는지 확인합니다.

## 라이센스

이 프로젝트는 YOLOv5와 동일한 라이센스(AGPL-3.0)를 따릅니다.

## 참고 자료

-   YOLOv5: https://github.com/ultralytics/yolov5
-   Arduino: https://www.arduino.cc/
-   Adafruit NeoPixel: https://github.com/adafruit/Adafruit_NeoPixel
