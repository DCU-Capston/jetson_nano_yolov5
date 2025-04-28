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
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        
        # 연결 시도
        self.connect()
    
    def connect(self):
        """아두이노에 연결 시도"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                time.sleep(0.5)
                
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # 아두이노 리셋 후 안정화 대기
            self.connected = True
            self.reconnect_attempts = 0
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
            # 응답 읽기 실패시 연결 상태 확인
            self._check_connection()
    
    def _check_connection(self):
        """연결 상태 확인 및 재연결 시도"""
        try:
            # 포트가 열려있는지 확인
            if not self.serial_conn or not self.serial_conn.is_open:
                self.connected = False
                
            # DTR(Data Terminal Ready) 상태 확인 
            self.serial_conn.dtr
            return True
        except Exception:
            self.connected = False
            print("아두이노 연결이 끊어졌습니다. 재연결을 시도합니다.")
            
            # 재연결 시도
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                print(f"재연결 시도 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                time.sleep(1)
                self.connect()
            else:
                print(f"최대 재연결 시도 횟수({self.max_reconnect_attempts})를 초과했습니다.")
            
            return self.connected
    
    def send_command(self, command):
        """
        아두이노에 명령 전송
        
        Args:
            command (str): 전송할 명령
                '0': 녹색 LED (감지 없음)
                '1': 빨간색 LED (감지됨)
        """
        if not self.connected:
            if not self._check_connection():
                print("아두이노에 연결되어 있지 않습니다.")
                return False
        
        # 같은 명령이 연속적으로 발생하면 중복 전송하지 않음
        if command == self.last_command:
            return True
            
        try:
            # 명령에 개행문자 추가하여 아두이노가 확실히 인식하도록 함
            self.serial_conn.write((command + '\n').encode())
            self.serial_conn.flush()  # 버퍼 내용 즉시 전송
            self.last_command = command
            print(f"아두이노에 명령 전송: {command}")
            
            # 응답 읽기
            time.sleep(0.1)  # 응답 대기 시간
            self._read_response()
            
            return True
        except Exception as e:
            print(f"명령 전송 실패: {e}")
            # 명령 전송 실패시 연결 확인 및 재시도
            if self._check_connection() and self.reconnect_attempts < self.max_reconnect_attempts:
                print("명령 재전송 시도...")
                time.sleep(0.5)
                return self.send_command(command)
            return False
    
    def set_green(self):
        """LED를 녹색으로 설정 (감지 없음)"""
        return self.send_command('0')
    
    def set_red(self):
        """LED를 빨간색으로 설정 (감지됨)"""
        return self.send_command('1')


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
        
        # 빨간색 (감지됨)
        print("빨간색 LED")
        controller.set_red()
        time.sleep(2)
        
        # 다시 초록색으로
        print("초록색 LED (테스트 종료)")
        controller.set_green()
        
    except KeyboardInterrupt:
        print("테스트가 중단되었습니다.")
    finally:
        controller.disconnect() 