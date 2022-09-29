#include <SPI.h>
#include <RH_RF95.h>

RH_RF95 rf95(8, 3); // Adafruit Feather M0 with RFM95
//RH_RF95 rf95;
int SF_hold = 8;
uint8_t SF[] = "8";                      // <= SF

int BW_hold = 125000;
uint8_t BW[] = "125000";              // <= BW

int delayTable[6] = {51, 93, 164, 329, 577, 1155};
int beacon_delay = (delayTable[SF_hold - 7] / (BW_hold / 125000)) * 3.5;

void setup() 
{
    Serial.begin(9600);
    
    if (!rf95.init())
      Serial.println("init failed");
      
    pinMode(LED_BUILTIN, OUTPUT);

    // Default, config messages sent using SF = 8 and BW = 250000
    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(8);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(250000);
    
    Serial.println("Sending to rf95_server");
    // Send a message to rf95_server
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
    rf95.send(SF, sizeof(SF));
    rf95.waitPacketSent();
    Serial.println(sizeof(SF));
    
    delay(500);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
    rf95.send(BW, sizeof(BW));
    rf95.waitPacketSent();
    Serial.println(sizeof(BW));

    if (!rf95.init())
      Serial.println("init failed");
    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(SF_hold);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(BW_hold);
    delay(beacon_delay + 200);
}

void loop()
{
  for (int i = 0; i < 16; i++) {
    delay(beacon_delay);
    digitalWrite(LED_BUILTIN, HIGH);
    uint8_t data3[] = "Tx";                     // <= Beacon
    rf95.send(data3, sizeof(data3));
    rf95.waitPacketSent();
    digitalWrite(LED_BUILTIN, LOW);
  }
  delay(1500);
  uint8_t data4[] = "Rst";                      // <= Reset Beacon
  rf95.send(data4, sizeof(data4));
  rf95.waitPacketSent();
  delay(1000);
  rf95.send(data4, sizeof(data4));              // <= Make sure all nodes reset
  rf95.waitPacketSent();
  delay(1000);
  rf95.send(data4, sizeof(data4));              // <= Really make sure all nodes reset
  rf95.waitPacketSent();
  while (true)
    delay(10000);
}
