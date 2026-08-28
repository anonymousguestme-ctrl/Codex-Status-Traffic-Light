// Codex Traffic Light for Arduino Uno R3 / ATmega328P.
// Module pins: GRN(GND), G, Y, R.

const uint8_t PIN_GREEN = 8;
const uint8_t PIN_YELLOW = 9;
const uint8_t PIN_RED = 10;

// Most 4-pin GND/G/Y/R traffic-light modules are active HIGH.
// Change to false if your LEDs behave in reverse.
const bool ACTIVE_HIGH = true;

const unsigned long HOST_TIMEOUT_MS = 15000;
unsigned long lastHostMessageMs = 0;
String commandBuffer;

void writeLamp(uint8_t pin, bool on) {
  digitalWrite(pin, on == ACTIVE_HIGH ? HIGH : LOW);
}
void setLights(bool green, bool yellow, bool red) {
  writeLamp(PIN_GREEN, green);
  writeLamp(PIN_YELLOW, yellow);
  writeLamp(PIN_RED, red);
}

void applyCommand(String command) {
  command.trim();
  command.toUpperCase();
  lastHostMessageMs = millis();

  if (command == "GREEN") {
    setLights(true, false, false);
    Serial.println(F("OK GREEN"));
  } else if (command == "YELLOW") {
    setLights(false, true, false);
    Serial.println(F("OK YELLOW"));
  } else if (command == "RED") {
    setLights(false, false, true);
    Serial.println(F("OK RED"));
  } else if (command == "OFF") {
    setLights(false, false, false);
    Serial.println(F("OK OFF"));
  } else if (command == "PING") {
    Serial.println(F("PONG CODEX_TRAFFIC_LIGHT_V1"));
  } else if (command.length() > 0) {
    Serial.print(F("ERR UNKNOWN_COMMAND "));
    Serial.println(command);
  }
}

void setup() {
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_YELLOW, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  setLights(false, true, false); // Yellow until the Windows host connects.

  Serial.begin(115200);
  commandBuffer.reserve(24);
  lastHostMessageMs = millis();
  Serial.println(F("READY CODEX_TRAFFIC_LIGHT_V1"));
}

void loop() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      applyCommand(commandBuffer);
      commandBuffer = "";
    } else if (c != '\r' && commandBuffer.length() < 32) {
      commandBuffer += c;
    }
  }

  if (millis() - lastHostMessageMs > HOST_TIMEOUT_MS) {
    setLights(false, true, false);
  }
}
