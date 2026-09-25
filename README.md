# LoRa Environmental Monitor

A wireless environmental monitoring system using a **Raspberry Pi 5**, **SX1278 LoRa modules**, **ESP32**, and a **DHT11 sensor** to read and transmit ambient temperature and humidity data.

---

## Overview

The system collects environmental data via a DHT11 sensor connected to a Raspberry Pi 5. The Pi packages and transmits this data wirelessly using an SX1278 LoRa transceiver at **433 MHz**. On the receiving end, an ESP32 equipped with a second SX1278 module intercepts the signal and prints the payload alongside signal parameters to the Serial Monitor.

```text
+-------+        +----------------+        +--------+
| DHT11 | -----> | Raspberry Pi 5 | -----> | SX1278 |
+-------+        +----------------+        +--------+
                                               |
                                         LoRa 433 MHz
                                               |
                                               v
+----------------+        +-------+        +--------+
| Serial Monitor | <----- | ESP32 | <----- | SX1278 |
+----------------+        +-------+        +--------+
```

---

## Features

* **Wireless Monitoring:** Long-range telemetry over the 433 MHz ISM band.
* **Low Power & High Reliability:** Uses CRC validation to prevent corrupted frames.
* **Signal Quality Metrics:** Output includes Real-time RSSI (Received Signal Strength Indicator) and SNR (Signal-to-Noise Ratio).
* **Cross-Platform:** Python-based transmitter pipeline on Raspberry Pi 5 paired with C++/Arduino firmware on ESP32.

---

## Hardware Requirements

* **Raspberry Pi 5** (Transmitter Node)
* **ESP32 Development Board** (Receiver Node)
* **2 × SX1278 LoRa Modules** (433 MHz)
* **DHT11** Temperature and Humidity Sensor
* Jumper Wires & Breadboard

---

## LoRa Configuration

Both transmitter and receiver modules must share identical RF configurations to communicate successfully:

| Parameter | Value |
| :--- | :--- |
| **Frequency** | 433 MHz |
| **Bandwidth** | 125 kHz |
| **Spreading Factor** | SF7 |
| **Coding Rate** | 4/5 |
| **CRC Status** | Enabled (`ON`) |
| **Sync Word** | `0x12` |
| **Preamble Length** | 8 |

---

## Pin Connections

### 1. DHT11 → Raspberry Pi 5

| DHT11 Pin | Raspberry Pi 5 Pin |
| :--- | :--- |
| **VCC** | 3.3V (Pin 1) |
| **DATA** | GPIO 17 (Pin 11) |
| **GND** | GND (Pin 9) |

---

### 2. SX1278 → ESP32 Receiver

| SX1278 Pin | ESP32 GPIO |
| :--- | :--- |
| **SCK** | GPIO 18 |
| **MISO** | GPIO 19 |
| **MOSI** | GPIO 23 |
| **NSS / CS** | GPIO 5 |
| **RESET** | GPIO 14 |
| **DIO0** | GPIO 26 |
| **VCC** | 3.3V |
| **GND** | GND |

---

## Example Output

### Transmitter (Raspberry Pi 5)
```text
Transmitting payload: Temperature:25.0C,Humidity:60.0%
Packet sent successfully.
```

### Receiver (ESP32 Serial Monitor)
```text
Packet received!
Message : Temperature:25.0C,Humidity:60.0%
RSSI    : -45 dBm
SNR     : 8.25 dB
```

---

## Software & Setup

### 1. Raspberry Pi 5 Setup
Make sure SPI is enabled via `sudo raspi-config` (`Interface Options` → `SPI`).

Install the required Python packages:
```bash
pip install spidev gpiod
```

Run the transmitter script:
```bash
python3 transmitter.py
```

### 2. ESP32 Setup
1. Open the Arduino IDE.
2. Ensure the **ESP32 Board Package** and an **SX1278 LoRa Library** (e.g., *Sandeep Mistry LoRa*) are installed.
3. Upload `receiver/receiver.ino` to your ESP32.
4. Open the Serial Monitor set to **`115200` baud**.

---

## Project Structure

```text
lora-environmental-monitor/
├── transmitter.py       # Python transmission script for RPi 5
├── receiver/
│   └── receiver.ino     # Arduino/C++ receiver code for ESP32
├── README.md            # Project documentation
└── LICENSE              # Open-source license
```

---

## Future Improvements

* [ ] Add an **OLED/LCD display** to the receiver node for standalone monitoring.
* [ ] Integrate additional sensors (e.g., BMP280 for pressure, MQ-135 for air quality).
* [ ] Log sensor telemetry to an SD card or SQLite database.
* [ ] Support multiple transmitter nodes with dynamic device addresses.
* [ ] Build a web dashboard for real-time data visualization.

---

## Author

**Athira M.**  
*Electronics and Communication Engineering*  
*Focus Areas:* Embedded Systems | IoT | Wireless Communication

---

