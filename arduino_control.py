#!/usr/bin/env python3
# 아두이노 LED 제어를 위한 직렬 통신 클래스

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
        except serial.SerialException as e:
            self.connected = False
            print(f"아두이노 연결 실패: {e}")
    
    def disconnect(self):
        """아두이노 연결 종료"""
        if self.connected and self.serial_conn:
            self.serial_conn.close()
            self.connected = False
            print("아두이노 연결이 종료되었습니다.")
    
    def send_command(self, command):
        """
        아두이노에 명령 전송
        
        Args:
            command (str): 전송할 명령
                '0': 녹색 LED (감지 없음)
                '1': 주황색 LED (감지됨)
                '2': 빨간색 LED (위험)
        """
        if not self.connected:
            print("아두이노에 연결되어 있지 않습니다.")
            return False
        
        # 같은 명령이 연속적으로 발생하면 중복 전송하지 않음
        if command == self.last_command:
            return True
            
        try:
            self.serial_conn.write(command.encode())
            self.last_command = command
            print(f"아두이노에 명령 전송: {command}")
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


# 테스트 코드
if __name__ == "__main__":
    # 아두이노 연결 포트는 시스템에 따라 다를 수 있음
    # Jetson Nano에서는 보통 '/dev/ttyACM0'
    # macOS에서는 '/dev/cu.usbmodem*'
    # Windows에서는 'COM*'
    controller = ArduinoController(port='/dev/ttyACM0')
    
    try:
        print("LED 색상 변경 테스트 시작...")
        
        # 초록색 (감지 없음)
        controller.set_green()
        time.sleep(2)
        
        # 주황색 (감지됨)
        controller.set_orange()
        time.sleep(2)
        
        # 빨간색 (위험)
        controller.set_red()
        time.sleep(2)
        
        # 다시 초록색으로
        controller.set_green()
        
    except KeyboardInterrupt:
        print("테스트가 중단되었습니다.")
    finally:
        controller.disconnect() 