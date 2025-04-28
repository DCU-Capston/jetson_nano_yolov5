#!/bin/bash
# Jetson Nano에 아두이노 제어 파일 설정 스크립트

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip3 install pyserial

# arduino_control.py 파일 생성
echo "아두이노 제어 모듈을 생성합니다..."
cat > arduino_control.py << 'EOL'
#!/usr/bin/env python3
# 아두이노 LED 제어를 위한 직렬 통신 클래스
# WS2812B-64 LED 스트립 제어 지원

import serial
import time
import threading

class ArduinoController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1):
        """
        아두이노 컨트롤러 초기화
        
        Args:
            port (str): 아두이노 직렬 포트 (기본값: '/dev/ttyACM0', macOS에서는 '/dev/cu.usbmodem*' 형식일 수 있음)
            baudrate (int): 통신 속도 (기본값: 9600)
            timeout (int): 시리얼 통신 타임아웃 (초)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.connected = False
        self.last_command = '0'  # 초기 상태는 녹색 (감지 없음)
        
        # 연결 시도
        self.connect()
    
    def connect(self):
        """아두이노에 연결 시도"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # 아두이노 리셋 후 안정화 대기
            self.connected = True
            print(f"아두이노에 연결되었습니다. 포트: {self.port}")
            
            # 아두이노로부터 응답 읽기
            self._read_response()
            
        except serial.SerialException as e:
            self.connected = False
            print(f"아두이노 연결 실패: {e}")
    
    def disconnect(self):
        """아두이노 연결 종료"""
        if self.connected and self.serial_conn:
            self.serial_conn.close()
            self.connected = False
            print("아두이노 연결이 종료되었습니다.")
    
    def _read_response(self):
        """아두이노로부터 응답 읽기 (비동기)"""
        if not self.connected:
            return
            
        try:
            # 응답이 있으면 읽기
            while self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode('utf-8').strip()
                if response:
                    print(f"아두이노 응답: {response}")
        except Exception as e:
            print(f"응답 읽기 실패: {e}")
    
    def send_command(self, command):
        """
        아두이노에 명령 전송
        
        Args:
            command (str): 전송할 명령
                '0': 녹색 LED (감지 없음)
                '1': 주황색 LED (감지됨)
                '2': 빨간색 LED (위험)
                'p': 펄스 효과
        """
        if not self.connected:
            print("아두이노에 연결되어 있지 않습니다.")
            return False
        
        # 펄스 효과의 경우 항상 전송
        if command == 'p':
            try:
                self.serial_conn.write(command.encode())
                print(f"아두이노에 명령 전송: {command} (펄스 효과)")
                self._read_response()
                return True
            except Exception as e:
                print(f"명령 전송 실패: {e}")
                return False
        
        # 같은 명령이 연속적으로 발생하면 중복 전송하지 않음
        if command == self.last_command:
            return True
            
        try:
            self.serial_conn.write(command.encode())
            self.last_command = command
            print(f"아두이노에 명령 전송: {command}")
            
            # 응답 읽기
            self._read_response()
            
            return True
        except Exception as e:
            print(f"명령 전송 실패: {e}")
            return False
    
    def set_green(self):
        """LED를 녹색으로 설정 (감지 없음)"""
        return self.send_command('0')
    
    def set_orange(self):
        """LED를 주황색으로 설정 (감지됨)"""
        return self.send_command('1')
    
    def set_red(self):
        """LED를 빨간색으로 설정 (위험)"""
        return self.send_command('2')
    
    def pulse_effect(self):
        """현재 색상으로 펄스 효과 표시"""
        return self.send_command('p')


# 테스트 코드
if __name__ == "__main__":
    # 아두이노 연결 포트는 시스템에 따라 다를 수 있음
    # Jetson Nano에서는 보통 '/dev/ttyACM0'
    # macOS에서는 '/dev/cu.usbmodem*'
    # Windows에서는 'COM*'
    import argparse
    
    parser = argparse.ArgumentParser(description='아두이노 WS2812B-64 LED 제어 테스트')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='아두이노 포트')
    args = parser.parse_args()
    
    controller = ArduinoController(port=args.port)
    
    if not controller.connected:
        print("아두이노 연결 실패. 포트를 확인하세요.")
        exit(1)
    
    try:
        print("WS2812B-64 LED 색상 변경 테스트 시작...")
        
        # 초록색 (감지 없음)
        print("초록색 LED")
        controller.set_green()
        time.sleep(2)
        
        # 펄스 효과
        print("초록색 펄스 효과")
        controller.pulse_effect()
        time.sleep(3)
        
        # 주황색 (감지됨)
        print("주황색 LED")
        controller.set_orange()
        time.sleep(2)
        
        # 펄스 효과
        print("주황색 펄스 효과")
        controller.pulse_effect()
        time.sleep(3)
        
        # 빨간색 (위험)
        print("빨간색 LED")
        controller.set_red()
        time.sleep(2)
        
        # 펄스 효과
        print("빨간색 펄스 효과")
        controller.pulse_effect()
        time.sleep(3)
        
        # 다시 초록색으로
        print("초록색 LED (테스트 종료)")
        controller.set_green()
        
    except KeyboardInterrupt:
        print("테스트가 중단되었습니다.")
    finally:
        controller.disconnect()
EOL

# 테스트 스크립트 생성
echo "테스트 스크립트를 생성합니다..."
cat > test_arduino_connection.py << 'EOL'
#!/usr/bin/env python3
# 아두이노 연결 테스트 스크립트 - WS2812B-64 LED 지원

import time
import argparse
import os
import glob

try:
    from arduino_control import ArduinoController
    arduino_module_exists = True
except ImportError:
    arduino_module_exists = False
    print("아두이노 제어 모듈을 찾을 수 없습니다. arduino_control.py 파일이 경로에 있는지 확인하세요.")

def list_serial_ports():
    """
    시스템에서 사용 가능한 시리얼 포트 목록을 반환합니다.
    """
    if os.name == 'nt':  # Windows
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif os.name == 'posix':  # Linux, macOS, etc.
        ports = glob.glob('/dev/tty[A-Za-z]*')
    else:
        raise EnvironmentError('지원되지 않는 플랫폼입니다')
    
    result = []
    for port in ports:
        if 'USB' in port or 'ACM' in port or 'COM' in port:
            result.append(port)
    
    return result

def test_arduino_connection(port, test_mode="basic", cycle_count=3, delay=1.0):
    """
    아두이노 연결을 테스트하고 LED 색상을 제어합니다.
    
    Args:
        port (str): 아두이노 시리얼 포트
        test_mode (str): 테스트 모드 (basic, advanced, pulse)
        cycle_count (int): LED 색상 순환 횟수
        delay (float): 각 색상 사이의 지연 시간(초)
    """
    if not arduino_module_exists:
        print("아두이노 제어 모듈을 가져올 수 없어 테스트를 수행할 수 없습니다.")
        return False
    
    try:
        print(f"아두이노 포트 {port}에 연결 시도 중...")
        arduino = ArduinoController(port=port)
        
        if not arduino.connected:
            print(f"아두이노 포트 {port}에 연결할 수 없습니다.")
            return False
        
        print(f"아두이노 포트 {port}에 연결되었습니다.")
        
        if test_mode == "basic":
            print(f"기본 LED 색상 테스트 시작 (순환 횟수: {cycle_count})...")
            
            for cycle in range(cycle_count):
                print(f"사이클 {cycle + 1}/{cycle_count}")
                
                print("초록색 LED")
                arduino.set_green()
                time.sleep(delay)
                
                print("주황색 LED")
                arduino.set_orange()
                time.sleep(delay)
                
                print("빨간색 LED")
                arduino.set_red()
                time.sleep(delay)
            
            print("초록색 LED (테스트 종료)")
            arduino.set_green()
        
        elif test_mode == "advanced":
            print("고급 LED 색상 테스트 시작...")
            
            # 초록색 -> 주황색 -> 빨간색 -> 초록색 테스트
            print("초록색 LED")
            arduino.set_green()
            time.sleep(delay)
            
            print("주황색 LED")
            arduino.set_orange()
            time.sleep(delay)
            
            print("빨간색 LED")
            arduino.set_red()
            time.sleep(delay)
            
            print("초록색 LED")
            arduino.set_green()
            time.sleep(delay)
            
        elif test_mode == "pulse":
            print("펄스 효과 테스트 시작...")
            
            # 초록색 + 펄스
            print("초록색 LED + 펄스 효과")
            arduino.set_green()
            time.sleep(0.5)
            arduino.pulse_effect()
            time.sleep(delay)
            
            # 주황색 + 펄스
            print("주황색 LED + 펄스 효과")
            arduino.set_orange()
            time.sleep(0.5)
            arduino.pulse_effect()
            time.sleep(delay)
            
            # 빨간색 + 펄스
            print("빨간색 LED + 펄스 효과")
            arduino.set_red()
            time.sleep(0.5)
            arduino.pulse_effect()
            time.sleep(delay)
            
            # 다시 초록색으로
            print("초록색 LED")
            arduino.set_green()
        
        else:
            print(f"알 수 없는 테스트 모드: {test_mode}")
            arduino.disconnect()
            return False
        
        arduino.disconnect()
        print("아두이노 연결 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"아두이노 테스트 중 오류 발생: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='아두이노 WS2812B-64 LED 제어 테스트')
    parser.add_argument('--port', type=str, help='아두이노 시리얼 포트')
    parser.add_argument('--cycles', type=int, default=3, help='LED 색상 순환 횟수 (기본값: 3)')
    parser.add_argument('--delay', type=float, default=1.0, help='각 색상 사이의 지연 시간(초) (기본값: 1.0)')
    parser.add_argument('--mode', type=str, default='basic', choices=['basic', 'advanced', 'pulse'], 
                        help='테스트 모드 (basic: 기본 색상, advanced: 고급 색상 변환, pulse: 펄스 효과)')
    parser.add_argument('--scan', action='store_true', help='사용 가능한 시리얼 포트 스캔')
    
    args = parser.parse_args()
    
    if args.scan:
        print("사용 가능한 시리얼 포트 스캔 중...")
        ports = list_serial_ports()
        
        if ports:
            print("다음 시리얼 포트를 찾았습니다:")
            for port in ports:
                print(f"  - {port}")
            print("\n아두이노 테스트를 실행하려면 다음 명령을 사용하세요:")
            print(f"  python {__file__} --port <포트명>")
        else:
            print("사용 가능한 시리얼 포트를 찾을 수 없습니다.")
        return
    
    # 포트가 지정되지 않은 경우 자동 감지 시도
    if not args.port:
        print("포트가 지정되지 않았습니다. 자동 감지를 시도합니다...")
        ports = list_serial_ports()
        
        if not ports:
            print("사용 가능한 시리얼 포트를 찾을 수 없습니다.")
            print("--port 옵션을 사용하여 아두이노 포트를 직접 지정하세요.")
            return
        
        # Jetson Nano에서 아두이노 포트는 일반적으로 /dev/ttyACM0
        for port in ports:
            if 'ACM' in port:
                args.port = port
                print(f"아두이노 포트를 {port}로 자동 감지했습니다.")
                break
        else:
            args.port = ports[0]
            print(f"아두이노 포트를 {args.port}로 선택했습니다 (첫 번째 사용 가능한 포트).")
    
    # 아두이노 연결 테스트
    test_arduino_connection(args.port, args.mode, args.cycles, args.delay)

if __name__ == "__main__":
    main()
EOL

# 실행 권한 부여
chmod +x arduino_control.py
chmod +x test_arduino_connection.py

echo "아두이노 디렉토리를 생성합니다..."
mkdir -p arduino_led_control

cat > arduino_led_control/led_control.ino << 'EOL'
// WS2812B-64 LED 스트립 제어를 위한 아두이노 코드
// Jetson Nano로부터 객체 감지 신호를 받아 LED 색상을 제어합니다

#include <Adafruit_NeoPixel.h>

// WS2812B LED 설정
#define LED_PIN     6     // LED 데이터 핀
#define LED_COUNT   64    // LED 개수 (WS2812B-64)

// 효과 설정
#define TRANSITION_DURATION 300  // 색상 전환 시간 (밀리초)
#define USE_SMOOTH_TRANSITION true // 부드러운 색상 전환 효과 사용 여부

// 상태 변수
char command;
int detectionLevel = 0; // 0: 감지 없음(초록), 1: 감지(주황), 2: 위험(빨강)

// 색상 정의
uint32_t GREEN_COLOR;
uint32_t ORANGE_COLOR;
uint32_t RED_COLOR;

// NeoPixel 객체 초기화
// NEO_GRB: WS2812B LED의 색상 순서 (Green-Red-Blue)
// NEO_KHZ800: WS2812B 통신 속도
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // 시리얼 통신 시작 (9600bps)
  Serial.begin(9600);
  
  // NeoPixel 초기화
  strip.begin();
  strip.setBrightness(50); // 밝기 설정 (0-255)
  strip.show(); // 모든 픽셀 끄기로 초기화
  
  // 색상 초기화
  GREEN_COLOR = strip.Color(0, 255, 0);   // RGB: 초록색
  ORANGE_COLOR = strip.Color(255, 165, 0); // RGB: 주황색
  RED_COLOR = strip.Color(255, 0, 0);     // RGB: 빨간색
  
  // 초기 LED 색상은 초록색으로 설정
  setColor(GREEN_COLOR);
  
  Serial.println("WS2812B-64 LED 제어 시작");
}

void loop() {
  // 시리얼 통신으로부터 명령 수신
  if (Serial.available() > 0) {
    command = Serial.read();
    
    // 명령에 따라 LED 색상 변경
    if (command == '0') {
      // 감지 없음 - 초록색
      detectionLevel = 0;
      if (USE_SMOOTH_TRANSITION) {
        fadeToColor(GREEN_COLOR, TRANSITION_DURATION);
      } else {
        setColor(GREEN_COLOR);
      }
      Serial.println("상태: 감지 없음 (초록색)");
    } 
    else if (command == '1') {
      // 감지됨 - 주황색
      detectionLevel = 1;
      if (USE_SMOOTH_TRANSITION) {
        fadeToColor(ORANGE_COLOR, TRANSITION_DURATION);
      } else {
        setColor(ORANGE_COLOR);
      }
      Serial.println("상태: 감지됨 (주황색)");
    } 
    else if (command == '2') {
      // 위험 - 빨간색
      detectionLevel = 2;
      if (USE_SMOOTH_TRANSITION) {
        fadeToColor(RED_COLOR, TRANSITION_DURATION);
      } else {
        setColor(RED_COLOR);
      }
      Serial.println("상태: 위험 (빨간색)");
    }
    else if (command == 'p') {
      // 펄스 효과 - 현재 색상에 따라 펄스 효과 표시
      if (detectionLevel == 0) {
        pulseEffect(GREEN_COLOR, 3);
      } else if (detectionLevel == 1) {
        pulseEffect(ORANGE_COLOR, 3);
      } else {
        pulseEffect(RED_COLOR, 3);
      }
    }
  }
  
  // 위험 수준이 2(빨간색)인 경우 깜박임 효과 적용
  if (detectionLevel == 2) {
    static unsigned long lastBlinkTime = 0;
    static boolean blinkState = true;
    
    // 500ms마다 깜박임
    if (millis() - lastBlinkTime > 500) {
      lastBlinkTime = millis();
      blinkState = !blinkState;
      
      if (blinkState) {
        setColor(RED_COLOR);
      } else {
        setColor(strip.Color(0, 0, 0)); // 꺼짐
      }
    }
  }
  
  // 추가 로직이 필요한 경우 이곳에 작성
  delay(10); // 짧은 지연 시간
}

// 모든 LED에 단일 색상 설정
void setColor(uint32_t color) {
  for(int i=0; i<LED_COUNT; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

// 기본 색상 함수들
void setGreen() {
  setColor(GREEN_COLOR);
}

void setOrange() {
  setColor(ORANGE_COLOR);
}

void setRed() {
  setColor(RED_COLOR);
}

// 한 색상에서 다른 색상으로 부드럽게 전환
void fadeToColor(uint32_t color, int duration) {
  uint32_t oldColor = strip.getPixelColor(0); // 현재 색상 가져오기
  
  // 현재 색상이 없으면 그냥 바로 설정
  if (oldColor == 0) {
    setColor(color);
    return;
  }
  
  uint8_t oldR = (oldColor >> 16) & 0xFF;
  uint8_t oldG = (oldColor >> 8) & 0xFF;
  uint8_t oldB = oldColor & 0xFF;
  
  uint8_t newR = (color >> 16) & 0xFF;
  uint8_t newG = (color >> 8) & 0xFF;
  uint8_t newB = color & 0xFF;
  
  // 점진적으로 색상 변경
  for(int step=0; step<=20; step++) {
    uint8_t r = oldR + (newR - oldR) * step / 20;
    uint8_t g = oldG + (newG - oldG) * step / 20;
    uint8_t b = oldB + (newB - oldB) * step / 20;
    
    setColor(strip.Color(r, g, b));
    delay(duration / 20);
  }
  
  // 마지막에 정확한 색상으로 설정
  setColor(color);
}

// 펄스 효과 - 색상이 부드럽게 밝아졌다 어두워짐
void pulseEffect(uint32_t color, int count) {
  uint8_t r = (color >> 16) & 0xFF;
  uint8_t g = (color >> 8) & 0xFF;
  uint8_t b = color & 0xFF;
  
  for (int j=0; j<count; j++) {
    // 어두워짐
    for (int k=100; k>=20; k-=5) {
      setColor(strip.Color(r*k/100, g*k/100, b*k/100));
      delay(30);
    }
    
    // 밝아짐
    for (int k=20; k<=100; k+=5) {
      setColor(strip.Color(r*k/100, g*k/100, b*k/100));
      delay(30);
    }
  }
  
  // 원래 색상으로 복원
  setColor(color);
}
EOL

echo "설정이 완료되었습니다. 이제 다음 명령으로 YOLOv5 객체 감지와 아두이노 제어를 실행할 수 있습니다:"
echo "python3 detect.py --weights yolov5s.pt --source 0 --use-arduino"
echo
echo "아두이노 연결을 테스트하려면 다음 명령을 실행하세요:"
echo "python3 test_arduino_connection.py --scan" 