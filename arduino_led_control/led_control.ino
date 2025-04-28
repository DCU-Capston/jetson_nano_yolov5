// LED 제어를 위한 아두이노 코드
// Jetson Nano로부터 객체 감지 신호를 받아 LED 색상을 제어합니다

// RGB LED 핀 설정
const int RED_PIN = 9;    // 빨간색 LED 핀
const int GREEN_PIN = 10; // 초록색 LED 핀
const int BLUE_PIN = 11;  // 파란색 LED 핀

// 상태 변수
char command;
int detectionLevel = 0; // 0: 감지 없음(초록), 1: 감지(주황), 2: 위험(빨강)

void setup() {
  // LED 핀을 출력으로 설정
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  
  // 시리얼 통신 시작 (9600bps)
  Serial.begin(9600);
  
  // 초기 LED 색상은 초록색으로 설정
  setGreen();
}

void loop() {
  // 시리얼 통신으로부터 명령 수신
  if (Serial.available() > 0) {
    command = Serial.read();
    
    // 명령에 따라 LED 색상 변경
    if (command == '0') {
      // 감지 없음 - 초록색
      detectionLevel = 0;
      setGreen();
    } 
    else if (command == '1') {
      // 감지됨 - 주황색
      detectionLevel = 1;
      setOrange();
    } 
    else if (command == '2') {
      // 위험 - 빨간색
      detectionLevel = 2;
      setRed();
    }
  }
  
  // 추가 로직이 필요한 경우 이곳에 작성
  delay(10); // 짧은 지연 시간
}

// LED 색상 설정 함수들
void setGreen() {
  analogWrite(RED_PIN, 0);
  analogWrite(GREEN_PIN, 255);
  analogWrite(BLUE_PIN, 0);
}

void setOrange() {
  analogWrite(RED_PIN, 255);
  analogWrite(GREEN_PIN, 165);
  analogWrite(BLUE_PIN, 0);
}

void setRed() {
  analogWrite(RED_PIN, 255);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);
} 