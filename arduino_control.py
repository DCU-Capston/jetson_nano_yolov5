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
                '1': 빨간색 LED (감지됨)
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
    
    def set_red(self):
        """LED를 빨간색으로 설정 (감지됨)"""
        return self.send_command('1')
    
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
        
        # 빨간색 (감지됨)
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