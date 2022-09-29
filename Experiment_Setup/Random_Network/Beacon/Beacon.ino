#include <SPI.h>
#include <RH_RF95.h>

//RH_RF95 rf95(8, 3); // Adafruit Feather M0 with RFM95 
RH_RF95 rf95;

void setup() 
{
    Serial.begin(9600);
    
    if (!rf95.init())
      Serial.println("init failed");
      
    pinMode(LED_BUILTIN, OUTPUT);

    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(8);
    rf95.setTxPower(23);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(250000);
    
    Serial.println("Sending to rf95_server");
    // Send a message to rf95_server
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
    uint8_t data1[] = "10";                              // <= SF
    rf95.send(data1, sizeof(data1));
    Serial.println(sizeof(data1));
    
    delay(200);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    uint8_t data2[] = "250000";                          //  = BW
    rf95.send(data2, sizeof(data2));
    Serial.println(sizeof(data2));
    
    delay(200);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    uint8_t data3[] = "5";                               // pps
    rf95.send(data3, sizeof(data3));
    Serial.println(sizeof(data3));
    delay(200);
    digitalWrite(LED_BUILTIN, HIGH);
    
    rf95.waitPacketSent();
}

void loop()
{
  delay(1000);
}
