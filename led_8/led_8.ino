/*
  RGB 8x8 Dot Matrix - Emoticon Display

  4x 74HC595 shift registers, all sharing CLK, LATCH, and OE:
    Row 595:   8-bit one-hot row anode selector    (active HIGH)
    Red 595:   8-bit red column cathodes           (active LOW)
    Green 595: 8-bit green column cathodes         (active LOW)
    Blue 595:  8-bit blue column cathodes          (active LOW)

  74HC595 wiring (per chip):
    SER   -> respective Arduino data pin
    SRCLK -> D2 (CLK)
    RCLK  -> D3 (LATCH)
    SRCLR -> 5V
    OE    -> 5V (or GND depending on your wiring)
    QH'   -> not used

  Pin assignments:
    D2: CLK   (all 595s)
    D3: LATCH (all 595s)
    D4: Row   595 SER
    D5: Red   595 SER
    D6: Green 595 SER
    D7: Blue  595 SER

  SPI (from STM32):
    COPI -> D11 (MOSI)
    SCK  -> D13
    CS   -> D10
*/



#include <EduIntro.h>

#define bongbingpin 0
#define bingbongpin  1
#define CLK_PIN      2
#define LATCH_PIN    3
#define SER_ROW_PIN  4
#define SER_RED_PIN  5
#define SER_GRN_PIN  6
#define SER_BLU_PIN  7

LM35 hot(A0);
// Frame buffers
uint8_t fb_r[8] = {0};
uint8_t fb_g[8] = {0};
uint8_t fb_b[8] = {0};

struct Emoticon {
  uint8_t r[8];
  uint8_t g[8];
  uint8_t b[8];
};

const Emoticon emoticons[] = {
  // index 0: placeholder
  { { 0b11000011,
      0b11100111,
      0b01111110,
      0b00111100,
      0b00111100,
      0b01111110,
      0b11100111,
      0b1100001},  {0}, {0} },

  {
    {0},{ 0b00000001,
          0b00000011,
          0b00000110,
          0b10001100,
          0b11011000,
          0b01110000,
          0b00100000,
          0b00000000}, {0}  },

    {{0},{0},{
       0b00011000,
  0b00100100,
  0b00100100,
  0b01111110,
  0b01111110,
  0b01111110,
  0b01111110,
  0b00000000
    }},
    {{0b00011000,
  0b00111100,
  0b01100110,
  0b00000000,
  0b00011000,
  0b00111100,
  0b01100110,
  0b00000000},{  0b00000000,
  0b00000000,
  0b00000000,
  0b00000000,
  0b00011000,
  0b00111100,
  0b01100110,
  0b00000000},{0}}
};

const int NUM_EMOTICONS = sizeof(emoticons) / sizeof(emoticons[0]);

// Load emoticon by index into frame buffers
void loadEmoticon(uint8_t idx) {
  if (idx >= NUM_EMOTICONS) return;  // ignore out of range
  memcpy(fb_r, emoticons[idx].r, 8);
  memcpy(fb_g, emoticons[idx].g, 8);
  memcpy(fb_b, emoticons[idx].b, 8);
}

// ---- Display driver ----

uint8_t reverseByte(uint8_t b) {
  b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
  b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
  b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
  return b;
}

inline void shiftBit(bool row_bit, bool red_bit, bool grn_bit, bool blu_bit) {
  digitalWrite(SER_ROW_PIN, row_bit ? HIGH : LOW);
  digitalWrite(SER_RED_PIN, red_bit ? HIGH : LOW);
  digitalWrite(SER_GRN_PIN, grn_bit ? HIGH : LOW);
  digitalWrite(SER_BLU_PIN, blu_bit ? HIGH : LOW);
  digitalWrite(CLK_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(CLK_PIN, LOW);
  delayMicroseconds(1);
}

void driveRow(int row) {
  uint8_t red        = fb_r[row];
  uint8_t green      = reverseByte(fb_g[row]);
  uint8_t blue       = reverseByte(fb_b[row]);
  uint8_t row_onehot = (1 << (7 - row));

  // Blank
  digitalWrite(LATCH_PIN, LOW);
  for (int b = 7; b >= 0; b--)
    shiftBit(false, true, true, true);
  digitalWrite(LATCH_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(LATCH_PIN, LOW);

  // Real data
  for (int b = 7; b >= 0; b--) {
    shiftBit(
      (row_onehot >> b) & 1,
      !((red   >> b) & 1),
      !((green >> b) & 1),
      !((blue  >> b) & 1)
    );
  }

  digitalWrite(LATCH_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(LATCH_PIN, LOW);

  delayMicroseconds(800);
}





void setup() {
  pinMode(CLK_PIN,     OUTPUT);
  pinMode(LATCH_PIN,   OUTPUT);
  pinMode(SER_ROW_PIN, OUTPUT);
  pinMode(SER_RED_PIN, OUTPUT);
  pinMode(SER_GRN_PIN, OUTPUT);
  pinMode(SER_BLU_PIN, OUTPUT);

  pinMode(bingbongpin, INPUT);
  pinMode(bongbingpin, INPUT);
  pinMode(A1, INPUT);
  pinMode(12, OUTPUT);
  Serial.begin(9600);

  digitalWrite(CLK_PIN,   LOW);
  digitalWrite(LATCH_PIN, LOW);

  // Clear registers
  for (int b = 0; b < 8; b++) shiftBit(false, true, true, true);
  digitalWrite(LATCH_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(LATCH_PIN, LOW);
  int scanRow_idx = 0;
}



bool tempLocked = false;

void loop() {
  for (int i = 0; i < 8; i++) {
    driveRow(i);
  }

  bool a = digitalRead(bingbongpin);
  bool b = digitalRead(bongbingpin);
  int tempC = analogRead(A1) * 500 / 1023;
  Serial.println(tempC);

  if (tempLocked) {
    // Stay locked until both a and b are LOW (i.e. the D12-driven signal settles)
    loadEmoticon(3);
    digitalWrite(12, HIGH);
    Serial.println(a);
    Serial.println(b);
    if (a || b) {
      tempLocked = false;
      digitalWrite(12, LOW);
    }
    return;
  }

  if (tempC > 45 && !(a || b)) {
    tempLocked = true;
    loadEmoticon(3);
    digitalWrite(12, HIGH);
    return;
  }

  if (a || b) {
    if (a) loadEmoticon(0);
    else if (b) loadEmoticon(1);
  } else {
    loadEmoticon(2);
  }
}