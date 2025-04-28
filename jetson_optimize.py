#!/usr/bin/env python3
# 젯슨 나노용 YOLOv5 최적화 스크립트

import os
import argparse
import platform
import subprocess
import sys
from pathlib import Path

def print_info(msg):
    print(f"\033[32m[INFO] {msg}\033[0m")

def print_warn(msg):
    print(f"\033[33m[WARN] {msg}\033[0m")

def print_error(msg):
    print(f"\033[31m[ERROR] {msg}\033[0m")

def check_jetson():
    """젯슨 장치인지 확인합니다."""
    try:
        with open('/etc/nv_tegra_release', 'r') as f:
            return True
    except FileNotFoundError:
        return False

def optimize_power(mode='max'):
    """젯슨 나노의 전력 모드를 설정합니다."""
    if not check_jetson():
        print_warn("젯슨 장치가 아닙니다. 전력 최적화를 건너뜁니다.")
        return False
    
    modes = {
        'max': 0,    # 최대 성능
        'mid': 1,    # 10W 모드
        'min': 2     # 5W 모드
    }
    
    if mode not in modes:
        print_error(f"유효하지 않은 전력 모드: {mode}. 'max', 'mid', 'min' 중 하나를 사용하세요.")
        return False
    
    try:
        cmd = f"sudo nvpmodel -m {modes[mode]}"
        print_info(f"전력 모드 설정: {mode}")
        subprocess.run(cmd, shell=True, check=True)
        
        # 최대 클럭 설정
        if mode == 'max':
            print_info("최대 클럭 설정")
            subprocess.run("sudo jetson_clocks", shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        print_error("전력 모드 설정 중 오류가 발생했습니다.")
        return False

def download_model(model_size='s'):
    """모델을 다운로드합니다."""
    valid_sizes = ['n', 's', 'm', 'l', 'x']
    if model_size not in valid_sizes:
        print_error(f"유효하지 않은 모델 크기: {model_size}. {', '.join(valid_sizes)} 중 하나를 사용하세요.")
        return False
    
    model_file = f"yolov5{model_size}.pt"
    if os.path.exists(model_file):
        print_info(f"모델 파일이 이미 존재합니다: {model_file}")
        return True
    
    try:
        print_info(f"yolov5{model_size} 모델 다운로드 중...")
        import torch
        model = torch.hub.load('ultralytics/yolov5', f'yolov5{model_size}', pretrained=True)
        print_info(f"모델 다운로드 완료: {model_file}")
        return True
    except Exception as e:
        print_error(f"모델 다운로드 중 오류가 발생했습니다: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='젯슨 나노용 YOLOv5 최적화')
    parser.add_argument('--power', type=str, default='max', choices=['max', 'mid', 'min'],
                        help='전력 모드: max (최대 성능), mid (10W), min (5W)')
    parser.add_argument('--model', type=str, default='s', choices=['n', 's', 'm', 'l', 'x'],
                        help='모델 크기: n (가장 작음), s (작음), m (중간), l (큼), x (가장 큼)')
    parser.add_argument('--download', action='store_true', help='모델 다운로드')
    args = parser.parse_args()
    
    # 젯슨 나노 확인
    if check_jetson():
        print_info("젯슨 장치가 감지되었습니다.")
        
        # 환경 정보 표시
        try:
            print_info("시스템 정보:")
            subprocess.run("jetson_release", shell=True)
        except subprocess.CalledProcessError:
            print_warn("시스템 정보를 가져올 수 없습니다.")
        
        # 전력 모드 설정
        optimize_power(args.power)
    else:
        print_warn("젯슨 장치가 아닙니다. 일부 최적화가 적용되지 않을 수 있습니다.")
    
    # 모델 다운로드
    if args.download:
        download_model(args.model)
    
    print_info("최적화가 완료되었습니다.")
    print_info("YOLOv5 실행 예시:")
    print_info(f"python detect.py --weights yolov5{args.model}.pt --img 320 --conf 0.25 --source 0")

if __name__ == '__main__':
    main() 