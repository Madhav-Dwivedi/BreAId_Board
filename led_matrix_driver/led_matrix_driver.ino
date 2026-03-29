/*
  RGB 8x8 Dot Matrix - Emoticon Display

  16-bit chain (4x 195E):
    Bits 15-8: red columns,   bit 15 = col 1, bit 8 = col 8  (active LOW)
    Bits  7-0: green columns, bit  7 = col 1, bit 0 = col 8  (active LOW)

  12-bit chain (3x 194E):
    Bits 11-4: row anodes,      bit 11 = row 1, bit 4 = row 8 (active HIGH)
    Bits  3-0: blue cols 1-4,   bit  3 = col 1, bit 0 = col 4 (active LOW)

  Direct GPIO:
    D6: blue col 5
    D7: blue col 6
    D8: blue col 7
    D9: blue col 8

  Control pins:
    D2: shared CLK
    D3: shared active-low RST
    D4: 16-bit chain serial in
    D5: 12-bit chain serial in
*/

#define CLK_PIN     2
#define RST_PIN     3
#define SER_16_PIN  4
#define SER_12_PIN  5

// Blue columns 5-8 direct GPIO, index 0 = col 5 ... index 3 = col 8
const int BLUE_DIRECT_PINS[4] = {6, 7, 8, 9};

// ---- Frame buffer ----
// uint8_t fb_r[8], fb_g[8], fb_b[8];
uint8_t fb_r[8] = {
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  0
};

uint8_t fb_g[8] = {
  0b00000000,
  0b00000000,
  0b0,
  0b0,
  0b0,
  0b0,
  0b00000000,
  0b00000000
};

uint8_t fb_b[8] = {
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  0
};

// ---- Clock pulse ----
inline void clockPulse() {
  digitalWrite(CLK_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(CLK_PIN, LOW);
  delayMicroseconds(1);
}

// ---- Shift one bit into both chains simultaneously ----
inline void shiftBit(bool row_bit, bool col_bit) {
  digitalWrite(SER_12_PIN, row_bit ? HIGH : LOW);
  digitalWrite(SER_16_PIN, col_bit ? HIGH : LOW);
  clockPulse();
}

// ---- Drive one row ----
// 16 clock pulses total, interleaving both chains.
//
// 12-bit chain bit layout (MSB first, 16 pulses):
//   Pulses  1-4:  don't care (pushed out of chain)
//   Pulses  5-12: row one-hot (bits 11-4)
//   Pulses 13-16: ~blue cols 1-4 (bits 3-0, active LOW)
//
// 16-bit chain bit layout (MSB first, 16 pulses):
//   Pulses  1-8:  ~red cols 1-8   (active LOW)
//   Pulses  9-16: ~green cols 1-8 (active LOW)
enum Color { RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, WHITE };

struct Emoticon {
  const char* name;
  uint8_t rows[8];  // bit 7 = col 1, bit 0 = col 8; 1 = pixel ON
  Color color;
  unsigned long duration_ms;
};

const Emoticon emoticons[] = {
  {
    "Happy",
    {
      0b00111100,
      0b01000010,
      0b10100101,
      0b10000001,
      0b10100101,
      0b10011001,
      0b01000010,
      0b00111100,
    },
    YELLOW, 2000
  }
};

void driveRow(int row) {
  uint8_t red        = fb_r[row];
  uint8_t green      = fb_g[row];
  uint8_t blue       = fb_b[row];
  uint8_t blue_hi    = (blue >> 4) & 0x0F;  // cols 1-4 → shift register
  uint8_t blue_lo    = blue & 0x0F;          // cols 5-8 → direct GPIO

  uint8_t row_onehot = (1 << (7 - row));     // bit 7 = row 1 (top)

  // Deactivate direct blue pins before shifting (avoid ghosting)
  for (int c = 0; c < 4; c++) digitalWrite(BLUE_DIRECT_PINS[c], HIGH);

  // // Pulses 1-4: red bits 7-4 into 16-bit chain, zeros into 12-bit chain
  // for (int b = 3; b >= 0; b--)
  //   shiftBit(false, (red >> (b + 4)) & 1);

  // // Pulses 5-8: red bits 3-0 into 16-bit chain, row one-hot upper nibble into 12-bit chain
  // for (int b = 3; b >= 0; b--)
  //   shiftBit((row_onehot >> (b + 4)) & 1, (red >> b) & 1);

  // // Pulses 9-12: green bits 7-4 into 16-bit chain, row one-hot lower nibble into 12-bit chain
  // for (int b = 3; b >= 0; b--)
  //   shiftBit((row_onehot >> b) & 1, (green >> (b + 4)) & 1);

  // // Pulses 13-16: green bits 3-0 into 16-bit chain, ~blue cols 1-4 into 12-bit chain
  // for (int b = 3; b >= 0; b--)
  //   shiftBit(!((blue_hi >> b) & 1), (green >> b) & 1);

    // Pulses 1-4
  for (int b = 3; b >= 0; b--)
      shiftBit(false, !((red >> (b + 4)) & 1));

  // Pulses 5-8
  for (int b = 3; b >= 0; b--)
      shiftBit((row_onehot >> (b + 4)) & 1, !((red >> b) & 1));

  // Pulses 9-12
  for (int b = 3; b >= 0; b--)
      shiftBit((row_onehot >> b) & 1, !((green >> (b + 4)) & 1));

  // Pulses 13-16
  for (int b = 3; b >= 0; b--)
      shiftBit(!((blue_hi >> b) & 1), !((green >> b) & 1));

  // Set direct blue cols 5-8 (active LOW)
  for (int c = 0; c < 4; c++)
    digitalWrite(BLUE_DIRECT_PINS[c], (blue_lo >> (3 - c)) & 1 ? LOW : HIGH);
}

// ---- Setup ----
void setup() {
  pinMode(CLK_PIN,    OUTPUT);
  pinMode(RST_PIN,    OUTPUT);
  pinMode(SER_16_PIN, OUTPUT);
  pinMode(SER_12_PIN, OUTPUT);
  digitalWrite(CLK_PIN,    LOW);
  digitalWrite(SER_16_PIN, LOW);
  digitalWrite(SER_12_PIN, LOW);

  for (int c = 0; c < 4; c++) {
    pinMode(BLUE_DIRECT_PINS[c], OUTPUT);
    digitalWrite(BLUE_DIRECT_PINS[c], HIGH);
  }

  // Reset all registers
  digitalWrite(RST_PIN, LOW);
  delay(100);
  digitalWrite(RST_PIN, HIGH);
}

// ---- Main loop ----
// fb_r, fb_g, fb_b are exposed globally -- fill them however you like
// then just let the loop multiplex

int scanRow_idx = 0;

void loop() {
  driveRow(scanRow_idx);
  scanRow_idx = (scanRow_idx + 1) % 8;
  delayMicroseconds(1000);
}