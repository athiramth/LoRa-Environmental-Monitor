#include <SPI.h>
#include <LoRa.h>

// ============================================================
// SX1278 / ESP32 wiring
// Change these pins if your wiring is different
// ============================================================

#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23
#define LORA_SS     5
#define LORA_RST   14
#define LORA_DIO0  26

#define LORA_FREQUENCY 433E6

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("ESP32 LoRa Receiver");
  Serial.println("--------------------");

  // SPI
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);

  // LoRa pins
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  // Start LoRa
  if (!LoRa.begin(LORA_FREQUENCY)) {
    Serial.println("LoRa initialization FAILED!");
    while (1);
  }

  // Same settings as Raspberry Pi transmitter
  LoRa.setSignalBandwidth(125E3);  // 125 kHz
  LoRa.setSpreadingFactor(7);      // SF7
  LoRa.setCodingRate4(5);           // 4/5
  LoRa.enableCrc();                 // CRC ON
  LoRa.setSyncWord(0x12);           // Sync Word 0x12

  Serial.println("LoRa initialized successfully");
  Serial.println("Frequency : 433 MHz");
  Serial.println("Bandwidth : 125 kHz");
  Serial.println("SF        : 7");
  Serial.println("CR        : 4/5");
  Serial.println("CRC       : ON");
  Serial.println("Sync Word : 0x12");
  Serial.println();
  Serial.println("Waiting for packets...");
}

void loop() {

  int packetSize = LoRa.parsePacket();

  if (packetSize) {

    Serial.println("Packet received!");

    String receivedMessage = "";

    while (LoRa.available()) {
      receivedMessage += (char)LoRa.read();
    }

    Serial.print("Message : ");
    Serial.println(receivedMessage);

    Serial.print("RSSI    : ");
    Serial.print(LoRa.packetRssi());
    Serial.println(" dBm");

    Serial.print("SNR     : ");
    Serial.print(LoRa.packetSnr());
    Serial.println(" dB");

    Serial.println("--------------------");
  }
}
