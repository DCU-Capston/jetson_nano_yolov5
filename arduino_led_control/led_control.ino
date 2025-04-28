// WS2812B-64 LED 스트립 제어를 위한 아두이노 코드
// Jetson Nano로부터 객체 감지 신호를 받아 LED 색상을 제어합니다

#include <Adafruit_NeoPixel.h>

// WS2812B LED 설정
#define LED_PIN     6     // LED 데이터 핀
#define LED_COUNT   64    // LED 개수 (WS2812B-64)

// 효과 설정
#define TRANSITION_DURATION 300  // 색상 전환 시간 (밀리초)
#define USE_SMOOTH_TRANSITION true // 부드러운 색상 전환 효과 사용 여부
#define CIRCLE_RADIUS 4    // 원형 패턴의 반지름

// 상태 변수
char command = '0';
int detectionLevel = 0; // 0: 감지 없음(초록), 1: 감지됨(빨강)
unsigned long lastCommandTime = 0;
unsigned long serialTimeout = 1000; // 시리얼 타임아웃(밀리초)

// 색상 정의
uint32_t GREEN_COLOR;
uint32_t RED_COLOR;
uint32_t BLACK_COLOR;

// NeoPixel 객체 초기화
// NEO_GRB: WS2812B LED의 색상 순서 (Green-Red-Blue)
// NEO_KHZ800: WS2812B 통신 속도
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // 먼저 LED 초기화 (통신 시작 전에)
  strip.begin();
  strip.setBrightness(50); // 밝기 설정 (0-255)
  strip.show(); // 모든 픽셀 끄기로 초기화
  
  // 색상 초기화
  GREEN_COLOR = strip.Color(0, 255, 0);   // RGB: 초록색
  RED_COLOR = strip.Color(255, 0, 0);     // RGB: 빨간색
  BLACK_COLOR = strip.Color(0, 0, 0);     // RGB: 검정색 (꺼짐)
  
  // 초기 LED 색상은 초록색 원형으로 설정
  setCirclePattern(GREEN_COLOR);
  
  // 시리얼 통신 시작 (9600bps)
  Serial.begin(9600);
  while (!Serial) {
    ; // 시리얼 포트가 연결될 때까지 대기 (USB 연결만 해당)
  }
  
  // 초기화 메시지 전송
  Serial.println("WS2812B-64 LED 제어 시작 (원형 패턴)");
  // 핑 메시지 전송 (연결 확인용)
  Serial.println("PING");
}

void loop() {
  // 시리얼 통신으로부터 명령 수신
  receiveSerialCommand();
  
  // 객체가 감지된 경우 (빨간색) 깜박임 효과 적용
  if (detectionLevel == 1) {
    static unsigned long lastBlinkTime = 0;
    static boolean blinkState = true;
    
    // 500ms마다 깜박임
    if (millis() - lastBlinkTime > 500) {
      lastBlinkTime = millis();
      blinkState = !blinkState;
      
      if (blinkState) {
        setCirclePattern(RED_COLOR);
      } else {
        setCirclePattern(BLACK_COLOR); // 꺼짐
      }
    }
  }
  
  // 주기적으로 핑 전송 (연결 상태 확인용)
  static unsigned long lastPingTime = 0;
  if (millis() - lastPingTime > 5000) { // 5초마다
    lastPingTime = millis();
    Serial.println("PING");
  }
  
  // 시리얼 통신이 장시간 없을 경우 기본 상태(녹색)로 복귀
  if (millis() - lastCommandTime > serialTimeout && detectionLevel != 0) {
    detectionLevel = 0;
    setCirclePattern(GREEN_COLOR);
    Serial.println("시리얼 타임아웃: 기본 상태(녹색)로 복귀");
  }
  
  // 짧은 지연 시간
  delay(10);
}

// 시리얼 명령 수신 처리
void receiveSerialCommand() {
  String inputString = "";
  
  while (Serial.available() > 0) {
    // 마지막 명령 시간 갱신
    lastCommandTime = millis();
    
    // 한 문자씩 읽기
    char inChar = (char)Serial.read();
    
    // 개행문자는 명령의 끝으로 처리
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) {
        processCommand(inputString.charAt(0));
        inputString = "";
      }
    } else {
      // 명령 문자열에 추가
      inputString += inChar;
    }
    
    // 버퍼에 남은 데이터가 없으면 즉시 처리
    if (Serial.available() == 0 && inputString.length() > 0) {
      processCommand(inputString.charAt(0));
      inputString = "";
    }
  }
}

// 명령 처리
void processCommand(char cmd) {
  command = cmd;
  
  // 명령에 따라 LED 색상 변경
  if (command == '0') {
    // 감지 없음 - 초록색
    detectionLevel = 0;
    if (USE_SMOOTH_TRANSITION) {
      fadeToCirclePattern(GREEN_COLOR, TRANSITION_DURATION);
    } else {
      setCirclePattern(GREEN_COLOR);
    }
    Serial.println("상태: 감지 없음 (초록색)");
  } 
  else if (command == '1' || command == '2') {
    // 감지됨 - 빨간색 (1 또는 2 명령 모두 빨간색으로 처리)
    detectionLevel = 1;
    if (USE_SMOOTH_TRANSITION) {
      fadeToCirclePattern(RED_COLOR, TRANSITION_DURATION);
    } else {
      setCirclePattern(RED_COLOR);
    }
    Serial.println("상태: 감지됨 (빨간색)");
  }
  
  // 응답으로 현재 상태 전송
  Serial.print("현재 상태: ");
  Serial.println(detectionLevel);
}

// 모든 LED 지우기 (끄기)
void clearAllLEDs() {
  for(int i=0; i<LED_COUNT; i++) {
    strip.setPixelColor(i, BLACK_COLOR);
  }
  strip.show();
}

// 원형 패턴으로 LED 설정
void setCirclePattern(uint32_t color) {
  clearAllLEDs();
  
  // 8x8 매트릭스에서 중앙을 찾아 원형 패턴 생성
  int centerX = 3; // 중앙 X 좌표 (0-7)
  int centerY = 3; // 중앙 Y 좌표 (0-7)
  
  for(int y=0; y<8; y++) {
    for(int x=0; x<8; x++) {
      // 중앙으로부터의 거리 계산
      float distance = sqrt(pow(x - centerX, 2) + pow(y - centerY, 2));
      
      // 원형 패턴 내에 있으면 해당 픽셀 켜기
      if(distance <= CIRCLE_RADIUS) {
        int pixelIndex = y * 8 + x;  // 8x8 매트릭스에서 픽셀 인덱스 계산
        strip.setPixelColor(pixelIndex, color);
      }
    }
  }
  
  strip.show();
}

// 기본 색상 함수들
void setGreen() {
  setCirclePattern(GREEN_COLOR);
}

void setRed() {
  setCirclePattern(RED_COLOR);
}

// 한 색상에서 다른 색상으로 부드럽게 전환 (원형 패턴)
void fadeToCirclePattern(uint32_t color, int duration) {
  uint32_t oldColor = strip.getPixelColor(27); // 중앙 부근 픽셀에서 현재 색상 가져오기
  
  // 현재 색상이 없으면 그냥 바로 설정
  if (oldColor == 0) {
    setCirclePattern(color);
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
    
    setCirclePattern(strip.Color(r, g, b));
    delay(duration / 20);
  }
  
  // 마지막에 정확한 색상으로 설정
  setCirclePattern(color);
} 