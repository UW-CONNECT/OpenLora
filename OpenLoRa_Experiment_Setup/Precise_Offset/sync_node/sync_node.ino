#include <SPI.h>
#include <RH_RF95.h>

// globals
volatile byte state = LOW;
int num = 0;
int super_num = 0;

// test parameters
int repeats = 10;                 // number of repeats at same time offsets
int num_repeats = 11;             // total number of offsets
unsigned long incr = 24782;       // starting delay for collision     (replace incr and offset with 0 for constant offset node)
unsigned long offset = 24782;     // additional delay for each test (in uS)
uint8_t data[] = "Hello";         // data to transmit

// LoRa parameters
float freq = 915.0;               // Center frequency
uint8_t SF = 12;                  // Spreading Factor
long BW = 250000;                 // Bandwidth
RH_RF95 rf95(8, 3);               // RF95 object

void setup() {
  // Initialize RF95 transmitter
  if (!rf95.init())
    while(true) {
      delay(500);
    }
  rf95.setTxPower(23, false);
  rf95.setSpreadingFactor(SF);
  rf95.setFrequency(freq);
  rf95.setSignalBandwidth(BW);

  // Set interrupt and LED pins
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(A3, INPUT_PULLUP);
  attachInterrupt(A3, blink, RISING);
}

void loop() {
  if(state == HIGH) {

    // transmit message
    delayMicroseconds(incr);
    digitalWrite(LED_BUILTIN, HIGH);
    rf95.send(data, sizeof(data));
    rf95.waitPacketSent();
    state = LOW;
    digitalWrite(LED_BUILTIN, LOW);

    // increment delay count and delay
    num++;
    super_num++;
    if (num == repeats) {
      incr = incr + offset;
      num = 0;
    }
    if (super_num == num_repeats * repeats) {
      delay(10000);
    }
  }
}

// inturrupt routine
void blink() {
  state = HIGH;
}
