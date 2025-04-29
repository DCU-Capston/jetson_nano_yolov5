// 객체 감지 상태에 따른 LED 제어 아두이노 코드
// 객체 감지 없음: 초록색 LED, 객체 감지됨: 빨간색 LED

#include <Adafruit_NeoPixel.h>

// WS2812B LED 설정
#define LED_PIN     6     // LED 데이터 핀
#define LED_COUNT   64    // LED 개수 (WS2812B-64)

// 내장 LED 핀 (디버깅용)
#define BUILTIN_LED_PIN 13  // 대부분의 아두이노 보드의 내장 LED 핀

// 상태 변수
char command = '0';
int detectionLevel = 0;  // 0: 감지 없음(초록), 1: 감지됨(빨강)
unsigned long lastCommandTime = 0;
unsigned long serialTimeout = 5000;  // 시리얼 타임아웃(밀리초)

// 색상 정의
uint32_t GREEN_COLOR;
uint32_t RED_COLOR;

// NeoPixel 객체 초기화
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // 디버깅용 내장 LED 핀 초기화
  pinMode(BUILTIN_LED_PIN, OUTPUT);
  digitalWrite(BUILTIN_LED_PIN, LOW);
  
  // LED 초기화
  strip.begin();
  strip.setBrightness(50);  // 밝기 설정 (0-255)
  strip.show();  // 모든 픽셀 끄기로 초기화
  
  // 색상 초기화
  GREEN_COLOR = strip.Color(0, 255, 0);   // RGB: 초록색
  RED_COLOR = strip.Color(255, 0, 0);     // RGB: 빨간색
  
  // 초기 LED 색상은 초록색 설정
  setCirclePattern(GREEN_COLOR);
  
  // 시리얼 통신 시작 (9600bps)
  Serial.begin(9600);
  
  // 초기화 확인을 위해 내장 LED 깜박임
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUILTIN_LED_PIN, HIGH);
    delay(200);
    digitalWrite(BUILTIN_LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("준비 완료");
}

void loop() {
  // 시리얼 통신으로부터 명령 수신
  receiveSerialCommand();
  
  // 상태에 따라 LED 패턴 설정
  if (detectionLevel == 1) {
    // 감지됨 - 빨간색 원형 LED
    digitalWrite(BUILTIN_LED_PIN, HIGH);  // 내장 LED도 켜기
  } else {
    // 감지 없음 - 초록색 원형 LED
    digitalWrite(BUILTIN_LED_PIN, LOW);   // 내장 LED 끄기
  }
  
  // 시리얼 통신이 장시간 없을 경우 기본 상태(녹색)로 복귀
  if (millis() - lastCommandTime > serialTimeout && detectionLevel != 0) {
    detectionLevel = 0;
    setCirclePattern(GREEN_COLOR);
    Serial.println("시리얼 타임아웃: 기본 상태(녹색)로 복귀");
    digitalWrite(BUILTIN_LED_PIN, LOW);
  }
  
  // 짧은 지연 시간
  delay(10);
}

// 시리얼 명령 수신 처리
void receiveSerialCommand() {
  static String inputString = "";
  
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
    setCirclePattern(GREEN_COLOR);
    Serial.println("상태: 감지 없음 (초록색)");
  } 
  else if (command == '1') {
    // 감지됨 - 빨간색
    detectionLevel = 1;
    setCirclePattern(RED_COLOR);
    Serial.println("상태: 감지됨 (빨간색)");
  }
  
  // 응답으로 현재 상태 전송
  Serial.print("S:");
  Serial.println(detectionLevel);
}

// 원형 패턴으로 LED 설정
void setCirclePattern(uint32_t color) {
  // 모든 LED를 같은 색상으로 설정 (원형 패턴)
  for (int i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
} 