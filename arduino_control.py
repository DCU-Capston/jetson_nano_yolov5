#!/usr/bin/env python3
# 아두이노 LED 제어를 위한 직렬 통신 클래스
# WS2812B-64 LED 스트립 제어 지원

import serial
import time
import threading
import sys

class ArduinoController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1, debug=True):
        """
        아두이노 컨트롤러 초기화
        
        Args:
            port (str): 아두이노 직렬 포트 (기본값: '/dev/ttyACM0', macOS에서는 '/dev/cu.usbmodem*' 형식일 수 있음)
            baudrate (int): 통신 속도 (기본값: 9600)
            timeout (int): 시리얼 통신 타임아웃 (초)
            debug (bool): 디버그 메시지 출력 여부
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.connected = False
        self.last_command = '0'  # 초기 상태는 녹색 (감지 없음)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.debug = debug
        self.last_response_time = 0
        
        # 응답 수신 스레드 
        self.response_thread = None
        self.thread_running = False
        
        # 연결 시도
        self.connect()
    
    def debug_print(self, message):
        """디버그 메시지 출력"""
        if self.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [아두이노 컨트롤러] {message}")
    
    def connect(self):
        """아두이노에 연결 시도"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                time.sleep(0.5)
                
            self.debug_print(f"포트 {self.port}에 연결 시도 중...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # 아두이노 리셋 후 안정화 대기
            self.connected = True
            self.reconnect_attempts = 0
            print(f"아두이노에 연결되었습니다. 포트: {self.port}")
            
            # 아두이노로부터 초기 응답 읽기
            self._read_initial_response()
            
            # 응답 수신 스레드 시작
            self._start_response_thread()
            
        except serial.SerialException as e:
            self.connected = False
            print(f"아두이노 연결 실패: {e}")
    
    def disconnect(self):
        """아두이노 연결 종료"""
        # 스레드 종료
        self.thread_running = False
        if self.response_thread and self.response_thread.is_alive():
            self.response_thread.join(timeout=1.0)
        
        if self.connected and self.serial_conn:
            self.serial_conn.close()
            self.connected = False
            print("아두이노 연결이 종료되었습니다.")
    
    def _start_response_thread(self):
        """응답 수신을 위한 스레드 시작"""
        if self.response_thread and self.response_thread.is_alive():
            return
            
        self.thread_running = True
        self.response_thread = threading.Thread(target=self._response_reader, daemon=True)
        self.response_thread.start()
        self.debug_print("응답 수신 스레드가 시작되었습니다.")
    
    def _response_reader(self):
        """지속적으로 아두이노 응답을 읽는 스레드 함수"""
        while self.thread_running and self.connected:
            try:
                if self.serial_conn and self.serial_conn.is_open and self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if response:
                        print(f"아두이노 응답: {response}")
                        self.last_response_time = time.time()
                time.sleep(0.1)  # CPU 부하 줄이기
            except Exception as e:
                self.debug_print(f"응답 읽기 오류: {e}")
                self._check_connection()
                time.sleep(1)
    
    def _read_initial_response(self):
        """아두이노 초기 응답 읽기"""
        if not self.connected:
            return
            
        # 초기 응답 읽기 (최대 3초 대기)
        start_time = time.time()
        responses = []
        
        while time.time() - start_time < 3:
            try:
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if response:
                        print(f"아두이노 응답: {response}")
                        responses.append(response)
                        self.last_response_time = time.time()
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"초기 응답 읽기 실패: {e}")
                break
        
        return responses
    
    def _check_connection(self):
        """연결 상태 확인 및 재연결 시도"""
        try:
            # 포트가 열려있는지 확인
            if not self.serial_conn or not self.serial_conn.is_open:
                self.connected = False
                
            # DTR(Data Terminal Ready) 상태 확인 
            self.serial_conn.dtr
            
            # 마지막 응답 시간 확인 (60초 이상 응답 없으면 연결 끊김으로 간주)
            if time.time() - self.last_response_time > 60 and self.last_response_time > 0:
                self.debug_print("60초 이상 응답이 없어 연결이 끊긴 것으로 간주합니다.")
                self.connected = False
            
            return True
        except Exception:
            self.connected = False
            self.debug_print("아두이노 연결이 끊어졌습니다. 재연결을 시도합니다.")
            
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
        
        # 명령 재전송 시도를 위한 변수
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 명령에 개행문자 추가하여 아두이노가 확실히 인식하도록 함
                cmd_str = command + '\n'
                self.debug_print(f"명령 전송 시도: '{command}' (시도 {retry_count+1}/{max_retries})")
                
                # 버퍼 비우기
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # 명령 전송
                bytes_written = self.serial_conn.write(cmd_str.encode())
                self.serial_conn.flush()  # 버퍼 내용 즉시 전송
                
                self.last_command = command
                print(f"아두이노에 명령 전송: {command} ({bytes_written} 바이트)")
                
                # 응답 대기
                time.sleep(0.5)
                
                # 명령 성공으로 간주
                return True
                
            except Exception as e:
                print(f"명령 전송 실패: {e}")
                retry_count += 1
                
                # 마지막 시도가 아니면 재연결 시도
                if retry_count < max_retries:
                    print(f"재시도 중... ({retry_count}/{max_retries})")
                    self._check_connection()
                    time.sleep(1)
                else:
                    print("최대 재시도 횟수를 초과했습니다.")
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
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    args = parser.parse_args()
    
    controller = ArduinoController(port=args.port, debug=args.debug)
    
    if not controller.connected:
        print("아두이노 연결 실패. 포트를 확인하세요.")
        sys.exit(1)
    
    try:
        print("WS2812B-64 LED 색상 변경 테스트 시작...")
        
        # 초록색 (감지 없음)
        print("초록색 LED")
        controller.set_green()
        time.sleep(3)
        
        # 빨간색 (감지됨)
        print("빨간색 LED")
        controller.set_red()
        time.sleep(3)
        
        # 다시 초록색으로
        print("초록색 LED (테스트 종료)")
        controller.set_green()
        
    except KeyboardInterrupt:
        print("테스트가 중단되었습니다.")
    finally:
        controller.disconnect() 