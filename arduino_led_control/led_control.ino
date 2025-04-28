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
int detectionLevel = 0; // 0: 감지 없음(초록), 1: 감지됨(빨강)

// 색상 정의
uint32_t GREEN_COLOR;
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
    else if (command == '1' || command == '2') {
      // 감지됨 - 빨간색 (1 또는 2 명령 모두 빨간색으로 처리)
      detectionLevel = 1;
      if (USE_SMOOTH_TRANSITION) {
        fadeToColor(RED_COLOR, TRANSITION_DURATION);
      } else {
        setColor(RED_COLOR);
      }
      Serial.println("상태: 감지됨 (빨간색)");
    }
    else if (command == 'p') {
      // 펄스 효과 - 현재 색상에 따라 펄스 효과 표시
      if (detectionLevel == 0) {
        pulseEffect(GREEN_COLOR, 3);
      } else {
        pulseEffect(RED_COLOR, 3);
      }
    }
  }
  
  // 객체가 감지된 경우 (빨간색) 깜박임 효과 적용
  if (detectionLevel == 1) {
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