#include <SPI.h>
#include <RH_RF95.h>

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
uint8_t len = sizeof(buf);

// LoRa parameters
float freq = 915.0;                 // Center frequency
uint8_t SF_hold = 8;                // Spreading Factor params (make sure match)
uint8_t SF[] = "8";
long BW_hold = 250000;              // Bandwidth params (make sure match)
uint8_t BW[] = "250000";
RH_RF95 rf95(8, 3);                 // RF95 object

void setup() 
{
    Serial.begin(9600);
    
    // Initialize RF95 transmitter
    if (!rf95.init())
      while(true) {
        delay(500);
      }

    // Default, config messages sent using SF = 8 and BW = 250000
    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(SF_hold);
    rf95.setFrequency(freq);
    rf95.setSignalBandwidth(BW_hold);

    // Set interrupt and LED pins
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    // begin roll call in 5 seconds
    Serial.println("Sending to rf95_server");
    delay(5000);
}

void loop()
{
  // send roll call beacons for all nodes
  for (int i = 0; i < 22; i++) {
    delay(150);
    digitalWrite(LED_BUILTIN, HIGH);
    uint8_t data3[] = {(i >> 8), (i & 0xFF)};   // <= Beacon
    rf95.send(data3, sizeof(data3));
    rf95.waitPacketSent();
    digitalWrite(LED_BUILTIN, LOW);

    // wait for response to roll call, print if present
    delay(0);
    if (rf95.available()) {
      if (rf95.recv(buf, &len)) {
        String rx_m = (char*)buf;
        Serial.println(buf[1]);
      }
    }
  }
  
  delay(1500);
  uint8_t data4[] = "Rst";                      // <= Tell nodes to reset
  rf95.send(data4, sizeof(data4));
  rf95.waitPacketSent();
  
  delay(100);
  rf95.send(data4, sizeof(data4));              // <= Tell nodes to reset
  rf95.waitPacketSent();
  
  delay(100);
  rf95.send(data4, sizeof(data4));              // <= Tell nodes to reset
  rf95.waitPacketSent();
  
  while (true)
    delay(1000);                                // <= End roll call sequence
}
