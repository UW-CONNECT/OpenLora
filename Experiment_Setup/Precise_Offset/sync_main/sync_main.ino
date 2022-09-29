// test parameters
int t_pin = 7;        // trigger pin
int period = 1200;    // time between inturrupts (transmissions)

void setup() {
  pinMode(t_pin, OUTPUT);
  delay(2000);
}

void loop() {
  digitalWrite(t_pin, LOW);
  delay(period);
  digitalWrite(t_pin, HIGH);
  delay(5);
}
