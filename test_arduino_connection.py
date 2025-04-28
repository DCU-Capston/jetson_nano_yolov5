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