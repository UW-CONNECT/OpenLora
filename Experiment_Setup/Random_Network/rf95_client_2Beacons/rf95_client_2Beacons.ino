#include <SPI.h>
#include <RH_RF95.h>
#include <math.h>

RH_RF95 rf95(8, 3); // Adafruit Feather M0 with RFM95 

uint8_t data[] = "Hello World";

int SF = 8;
int SF_norm = 8;

int BW = 250000;
int BW_norm = 250000;

double lamda_n;   // = 6;
int arr_len;      // = (lamda_n * 30) + 1;
int pkt_time;
int node_id = 20;

int tbl_125[6] = {52,93,165,330,578,1156};
int tbl_250[6] = {26,47,83,165,289,578};
int tbl_500[6] = {13,24,42,83,145,289};

boolean flag_B1 = true;
boolean flag_B2 = false;
boolean flag_tx = false;

unsigned long Time;
unsigned long delTime;

void setup() 
{
    Serial.begin(9600);
    if (!rf95.init())
      Serial.println("init failed");
    
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);
    randomSeed(node_id);

    rf95.setTxPower(23, false);
    rf95.setSpreadingFactor(SF_norm);
    rf95.setTxPower(23);
    rf95.setFrequency(915);
    rf95.setSignalBandwidth(BW_norm);
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
  }
  if (rf95.available()) {
    // Should be a message for us now
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    if (rf95.recv(buf, &len)) {
      String rx_m = (char*)buf;

      if(flag_B1 && !flag_B2) {
        if(rx_m == "6" || rx_m == "7" || rx_m == "8" || rx_m == "9" || rx_m == "10" || rx_m == "11" || rx_m == "12"){
          Serial.print("Received SF Value: ");
          Serial.println(rx_m);
          SF = rx_m.toInt();
          flag_tx = true;
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
          Serial.print("Received BW value Beacon: ");
          Serial.println(rx_m);
          BW = rx_m.toInt();
          flag_B1 = false;
          flag_B2 = false;
          Time = millis();
        }
        else{
          Serial.println("Invalid BW_value");
          Serial.println((char*)buf);
          flag_B1 = true;
          flag_B2 = false;
          flag_tx = false;
        }
      }
      else if (rx_m == "0.5" || rx_m == "1" || rx_m == "2" || rx_m == "3" || rx_m == "4" || rx_m == "5" || rx_m == "6") {
        Serial.println("Received lambda values!");
        lamda_n = rx_m.toDouble();
        Serial.println(lamda_n);
        if (!rf95.init())
          Serial.println("init failed");
        rf95.setTxPower(23, false);
        rf95.setSpreadingFactor(SF);
        rf95.setFrequency(915);
        rf95.setSignalBandwidth(BW);

        
        arr_len = (lamda_n * 30) + 1;
        int tx_time = 0;
        if (BW == 125000) {
          tx_time = tbl_125[SF - 7];
        } else if (BW == 250000) {
          tx_time = tbl_250[SF - 7];
        } else {
          tx_time = tbl_500[SF - 7];
        }
        
        tx_time = lamda_n * 30 * tx_time;
        if (tx_time > 30000) {
          Serial.println("Too Fast!!");
        } else {
          int del_time = 30000 - tx_time;
          Serial.println(del_time);
          
          int w = (del_time * 2) / (30 * lamda_n);
          Serial.println(w);
  
          for(int c = 1; c < arr_len; c++){
            delay(random(1,w));
            digitalWrite(LED_BUILTIN, HIGH);  
            rf95.send(data, sizeof(data));
            rf95.waitPacketSent();
            digitalWrite(LED_BUILTIN, LOW);  
          }
  
          Time = millis();
          Serial.println("Done!");
          if (!rf95.init())
            Serial.println("init failed");
          rf95.setTxPower(23, false);
          rf95.setSpreadingFactor(SF_norm);
          rf95.setFrequency(915);
          rf95.setSignalBandwidth(BW_norm);
          flag_B1 = true;
          flag_B2 = false;
        }
      }
      else if (rx_m == "Hello World") {
        Serial.println("ERROR: Received message from server");
        flag_B1 = true;
        flag_B2 = false;
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
        Time = millis();
      }
    }
  }
}
