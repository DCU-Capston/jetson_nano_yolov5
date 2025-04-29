#!/usr/bin/env python3
# 아두이노 LED 제어를 위한 직렬 통신 클래스
# 객체 감지 상태에 따라 LED 색상 제어

import serial
import time
import sys

class ArduinoController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1, debug=False):
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
        self.debug = debug
        
        # 연결 시도
        self.connect()
    
    def debug_print(self, message):
        """디버그 메시지 출력"""
        if self.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [아두이노] {message}")
    
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
            print(f"아두이노 연결됨: {self.port}")
            
            # 초기 응답 읽기
            self._read_initial_response()
            
        except serial.SerialException as e:
            self.connected = False
            print(f"아두이노 연결 실패: {e}")
    
    def disconnect(self):
        """아두이노 연결 종료"""
        if self.connected and self.serial_conn:
            self.serial_conn.close()
            self.connected = False
            self.debug_print("연결 종료됨")
    
    def _read_initial_response(self):
        """아두이노 초기 응답 읽기"""
        if not self.connected:
            return
            
        # 초기 응답 읽기 (최대 3초 대기)
        start_time = time.time()
        
        while time.time() - start_time < 3:
            try:
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if response:
                        self.debug_print(f"초기 응답: {response}")
                else:
                    time.sleep(0.1)
            except Exception as e:
                self.debug_print(f"초기 응답 읽기 실패: {e}")
                break
    
    def send_command(self, command):
        """
        아두이노에 명령 전송
        
        Args:
            command (str): 전송할 명령
                '0': 녹색 LED (감지 없음)
                '1': 빨간색 LED (감지됨)
        """
        if not self.connected:
            return False
        
        # 같은 명령이 연속으로 전송되면 무시
        if command == self.last_command:
            return True
            
        try:
            # 명령에 개행문자 추가하여 아두이노가 확실히 인식하도록 함
            cmd_str = command + '\n'
            self.debug_print(f"명령 전송: '{command}'")
            
            # 버퍼 비우기
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            # 명령 전송
            self.serial_conn.write(cmd_str.encode())
            self.serial_conn.flush()  # 버퍼 내용 즉시 전송
            
            self.last_command = command
            if command == '0':
                print("감지 없음: 초록색 설정")
            elif command == '1':
                print("객체 감지: 빨간색 설정")
            
            # 응답 대기
            time.sleep(0.2)
            
            return True
                
        except Exception as e:
            self.debug_print(f"명령 전송 실패: {e}")
            return False
    
    def set_green(self):
        """LED를 녹색으로 설정 (감지 없음)"""
        return self.send_command('0')
    
    def set_red(self):
        """LED를 빨간색으로 설정 (감지됨)"""
        return self.send_command('1')

# 라이브러리로 사용할 경우 여기서 중단
if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트 수행
    import argparse
    
    parser = argparse.ArgumentParser(description='Arduino LED 제어 테스트')
    parser.add_argument('--port', type=str, help='아두이노 시리얼 포트')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    args = parser.parse_args()
    
    # 포트가 지정되지 않은 경우 자동 감지 시도
    if not args.port:
        # macOS의 경우 일반적으로 /dev/cu.usbmodem* 형식
        if sys.platform == 'darwin':
            import glob
            ports = glob.glob('/dev/cu.usbmodem*')
            if ports:
                args.port = ports[0]
                print(f"아두이노 포트를 {args.port}로 자동 감지했습니다.")
            else:
                args.port = '/dev/ttyACM0'  # 기본값
        else:
            args.port = '/dev/ttyACM0'  # Linux 기본값
    
    # 컨트롤러 초기화
    controller = ArduinoController(port=args.port, debug=args.debug)
    
    if controller.connected:
        print("아두이노 연결 성공! 테스트를 시작합니다.")
        
        try:
            # 초록색 LED 설정
            print("초록색 LED 설정 중...")
            controller.set_green()
            time.sleep(2)
            
            # 빨간색 LED 설정
            print("빨간색 LED 설정 중...")
            controller.set_red()
            time.sleep(2)
            
            # 다시 초록색으로 복귀
            print("다시 초록색으로 복귀...")
            controller.set_green()
            
        except KeyboardInterrupt:
            print("테스트 중단됨")
        finally:
            # 연결 종료
            controller.disconnect()
            print("아두이노 연결 종료됨")
    else:
        print("아두이노에 연결할 수 없습니다.") 