#include <SPI.h>
#include <RH_RF95.h>
#include <math.h>

RH_RF95 rf95(8, 3); // Adafruit Feather M0 with RFM95 

uint8_t data[] = "Hello World";

int SF = 8;
int SF_norm = 8;
int BW = 250000;
int BW_norm = 250000;

double lamda_n;
int node_id = 12;

boolean flag_B1 = true;
boolean flag_B2 = false;

unsigned long Time;
unsigned long delTime;

int max_rand_delay = 50;

int delayTable[6] = {51, 93, 164, 329, 577, 1155};

void setup() 
{
    Serial.begin(9600);
    randomSeed(node_id);
    if (!rf95.init())
      Serial.println("init failed");
    
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(SF_norm);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(BW_norm);
    Time = millis();
}

void loop()
{
  delTime = millis();
  if (delTime - Time > 15000) {
    Serial.println("TIMEOUT, reset");
    if (!rf95.init())
      Serial.println("init failed");
    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(SF_norm);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(BW_norm);
    Time = millis();
    flag_B1 = true;
    flag_B2 = false;
    max_rand_delay = 50;
  }
  if (rf95.available()) {
    Serial.println("CP2");

    // Should be a message for us now
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    if (rf95.recv(buf, &len)) {
      String rx_m = (char*)buf;
      Serial.println(rx_m);

      if(flag_B1 && !flag_B2) {
        if(rx_m == "6" || rx_m == "7" || rx_m == "8" || rx_m == "9" || rx_m == "10" || rx_m == "11" || rx_m == "12"){
          Serial.print("Received SF Value: ");
          SF = rx_m.toInt();
          Serial.println(SF);
          flag_B1 = false;
          flag_B2 = true;
          Time = millis();
        }
        else if(buf[1] == (uint8_t)node_id) {
          Serial.println("Hey attendance!");
          uint8_t data2[] = {(node_id >> 8), (node_id & 0xFF)}; 
          rf95.send(data2, sizeof(data2));
          rf95.waitPacketSent();
        }
      }
      else if(!flag_B1 && flag_B2) {
        if(rx_m == "125000" || rx_m == "250000" || rx_m == "500000") {
          Serial.print("Received BW:");
          BW = rx_m.toInt();
          Serial.println(BW);
          if (!rf95.init())
            Serial.println("init failed");
          rf95.setTxPower(23, false);
          rf95.setSpreadingFactor(SF);
          rf95.setFrequency(915);
          rf95.setSignalBandwidth(BW);
          max_rand_delay = (delayTable[SF - 7] / (BW / 125000)) * 0.9;
          Serial.println(max_rand_delay);
          
          flag_B1 = false;
          flag_B2 = false;
        } else {
          Serial.println("Invalid BW");
          Serial.println((char*)buf);
          flag_B1 = true;
          flag_B2 = false;
        }
        Time = millis();
      } 
      else if(!flag_B1 && !flag_B2) {
        if (rx_m == "Tx" || rx_m == "Rst") {
          // begin transmission
          if (rx_m == "Tx") {
            Serial.println("Send");
            delay(random(1,max_rand_delay));
            digitalWrite(LED_BUILTIN, HIGH);  
            rf95.send(data, sizeof(data));
            rf95.waitPacketSent();
            digitalWrite(LED_BUILTIN, LOW);
            delay(max_rand_delay * 1.1);
          } else {
            Serial.println("Reset");
            if (!rf95.init())
              Serial.println("init failed");
            rf95.setTxPower(23, false);
            rf95.setSpreadingFactor(SF_norm);
            rf95.setFrequency(915);
            rf95.setSignalBandwidth(BW_norm);
            flag_B1 = true;
            flag_B2 = false;
            max_rand_delay = 50;
          }
          Time = millis();
        } else {
          Serial.println("ERROR: corrupted test");
//          rf95.setSpreadingFactor(SF_norm);
//          delay(50);
//          rf95.setSignalBandwidth(BW_norm);
//          delay(50);
//          flag_B1 = true;
//          flag_B2 = false;
//          max_rand_delay = 50;
          // Time = millis();
        }
      }
      else {
        Serial.println("recv failed");
        if (!rf95.init())
          Serial.println("init failed");
        rf95.setTxPower(23, false);
        rf95.setSpreadingFactor(SF_norm);
        rf95.setFrequency(915);
        rf95.setSignalBandwidth(BW_norm);
        flag_B1 = true;
        flag_B2 = false;
        max_rand_delay = 50;
        Time = millis();
      }
    }
  }
}
