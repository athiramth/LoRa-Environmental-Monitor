import time
import spidev
import gpiod


# ============================================================
# GPIO / DHT11
# ============================================================

GPIO_CHIP = "/dev/gpiochip4"
DHT_GPIO = 17


# ============================================================
# SPI
# ============================================================

spi = spidev.SpiDev()
spi.open(0, 0)

spi.max_speed_hz = 500000
spi.mode = 0
spi.no_cs = False


# ============================================================
# SX1278 REGISTERS
# ============================================================

REG_FIFO                    = 0x00
REG_OP_MODE                 = 0x01
REG_FRF_MSB                 = 0x06
REG_FRF_MID                 = 0x07
REG_FRF_LSB                 = 0x08
REG_PA_CONFIG               = 0x09
REG_PA_RAMP                 = 0x0A
REG_OCP                     = 0x0B
REG_LNA                     = 0x0C
REG_FIFO_ADDR_PTR           = 0x0D
REG_FIFO_TX_BASE_ADDR       = 0x0E
REG_FIFO_RX_BASE_ADDR       = 0x0F
REG_IRQ_FLAGS               = 0x12
REG_MODEM_CONFIG1           = 0x1D
REG_MODEM_CONFIG2           = 0x1E
REG_PREAMBLE_MSB            = 0x20
REG_PREAMBLE_LSB            = 0x21
REG_PAYLOAD_LENGTH          = 0x22
REG_MODEM_CONFIG3            = 0x26
REG_SYNC_WORD               = 0x39
REG_DETECTION_OPTIMIZE      = 0x31
REG_DETECTION_THRESHOLD     = 0x37
REG_DIO_MAPPING1            = 0x40
REG_VERSION                 = 0x42


# ============================================================
# IRQ
# ============================================================

IRQ_TX_DONE = 0x08


# ============================================================
# SPI FUNCTIONS
# ============================================================

def write_register(address, value):

    spi.xfer2([
        address | 0x80,
        value & 0xFF
    ])


def read_register(address):

    result = spi.xfer2([
        address & 0x7F,
        0x00
    ])

    return result[1]


# ============================================================
# LoRa SETUP
# ============================================================

def setup_lora():

    version = read_register(REG_VERSION)

    print(f"SX1278 version: 0x{version:02X}")

    if version != 0x12:
        raise RuntimeError(
            f"SX1278 not detected. Version = 0x{version:02X}"
        )

    # LoRa + sleep
    write_register(REG_OP_MODE, 0x80)

    time.sleep(0.01)

    # LoRa + standby
    write_register(REG_OP_MODE, 0x81)

    time.sleep(0.01)

    # --------------------------------------------------------
    # 433 MHz
    # --------------------------------------------------------

    frf = int((433000000 / 32000000) * (2 ** 19))

    write_register(REG_FRF_MSB, (frf >> 16) & 0xFF)
    write_register(REG_FRF_MID, (frf >> 8) & 0xFF)
    write_register(REG_FRF_LSB, frf & 0xFF)

    # --------------------------------------------------------
    # PA
    # --------------------------------------------------------

    write_register(REG_PA_CONFIG, 0x8F)
    write_register(REG_PA_RAMP, 0x09)
    write_register(REG_OCP, 0x2B)
    write_register(REG_LNA, 0x23)

    # --------------------------------------------------------
    # FIFO
    # --------------------------------------------------------

    write_register(REG_FIFO_TX_BASE_ADDR, 0x00)
    write_register(REG_FIFO_RX_BASE_ADDR, 0x00)

    # --------------------------------------------------------
    # Modem
    #
    # BW 125 kHz
    # CR 4/5
    # SF7
    # CRC ON
    # --------------------------------------------------------

    write_register(REG_MODEM_CONFIG1, 0x72)
    write_register(REG_MODEM_CONFIG2, 0x74)
    write_register(REG_MODEM_CONFIG3, 0x04)

    # Preamble = 8
    write_register(REG_PREAMBLE_MSB, 0x00)
    write_register(REG_PREAMBLE_LSB, 0x08)

    # Sync word
    write_register(REG_SYNC_WORD, 0x12)

    # SF7 detection settings
    write_register(REG_DETECTION_OPTIMIZE, 0x03)
    write_register(REG_DETECTION_THRESHOLD, 0x0A)

    # DIO0 = TxDone
    # DIO0 is not physically connected.
    write_register(REG_DIO_MAPPING1, 0x40)

    # Clear IRQ
    write_register(REG_IRQ_FLAGS, 0xFF)

    # Standby
    write_register(REG_OP_MODE, 0x81)

    time.sleep(0.01)


# ============================================================
# SEND LoRa PACKET
# ============================================================

def send_packet(message):

    data = message.encode("utf-8")

    if len(data) > 255:
        raise ValueError("Message too long")

    # Standby
    write_register(REG_OP_MODE, 0x81)

    # Clear IRQ flags
    write_register(REG_IRQ_FLAGS, 0xFF)

    # FIFO pointer = TX base
    write_register(REG_FIFO_ADDR_PTR, 0x00)

    # Write data
    for byte in data:
        write_register(REG_FIFO, byte)

    # Payload length
    write_register(REG_PAYLOAD_LENGTH, len(data))

    # Clear IRQ
    write_register(REG_IRQ_FLAGS, 0xFF)

    # TX mode
    write_register(REG_OP_MODE, 0x83)

    timeout = time.monotonic() + 5.0

    while True:

        irq = read_register(REG_IRQ_FLAGS)

        if irq & IRQ_TX_DONE:
            break

        if time.monotonic() > timeout:

            write_register(REG_OP_MODE, 0x81)

            raise RuntimeError("LoRa TX timeout")

        time.sleep(0.001)

    # Clear TxDone
    write_register(REG_IRQ_FLAGS, IRQ_TX_DONE)

    # Standby
    write_register(REG_OP_MODE, 0x81)


# ============================================================
# DHT11 READER
# ============================================================

def read_dht11():

    chip = gpiod.Chip(GPIO_CHIP)

    # --------------------------------------------------------
    # Pull DATA LOW for 20 ms
    # --------------------------------------------------------

    request = chip.request_lines(
        consumer="dht11",
        config={
            DHT_GPIO: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE
            )
        }
    )

    time.sleep(0.020)

    # Release DATA line
    request.release()

    # --------------------------------------------------------
    # Input mode
    # --------------------------------------------------------

    request = chip.request_lines(
        consumer="dht11",
        config={
            DHT_GPIO: gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT
            )
        }
    )

    # --------------------------------------------------------
    # DHT11 response:
    #
    # After host releases line:
    #
    #   sensor pulls LOW  ~80 us
    #   sensor pulls HIGH ~80 us
    #
    # GPIO ACTIVE = HIGH
    # GPIO INACTIVE = LOW
    #
    # Therefore wait while line is HIGH.
    # --------------------------------------------------------

    start_wait = time.monotonic_ns()

    while request.get_value(DHT_GPIO) == gpiod.line.Value.ACTIVE:

        if time.monotonic_ns() - start_wait > 5_000_000:

            request.release()
            chip.close()

            raise RuntimeError("No DHT11 response")

    # --------------------------------------------------------
    # Capture waveform
    # --------------------------------------------------------

    transitions = []

    last = request.get_value(DHT_GPIO)
    start = time.monotonic_ns()

    while time.monotonic_ns() - start < 8_000_000:

        value = request.get_value(DHT_GPIO)

        if value != last:

            now = time.monotonic_ns()

            transitions.append(
                (last, value, now)
            )

            last = value

    request.release()
    chip.close()

    # --------------------------------------------------------
    # Extract HIGH pulse durations
    # --------------------------------------------------------

    high_times = []

    high_start = None

    for old_value, new_value, timestamp in transitions:

        # LOW -> HIGH
        if (
            old_value == gpiod.line.Value.INACTIVE
            and new_value == gpiod.line.Value.ACTIVE
        ):

            high_start = timestamp

        # HIGH -> LOW
        elif (
            old_value == gpiod.line.Value.ACTIVE
            and new_value == gpiod.line.Value.INACTIVE
        ):

            if high_start is not None:

                duration = timestamp - high_start

                # DHT11:
                #
                # 0 = approximately 26-28 us
                # 1 = approximately 70 us
                #
                if 10_000 < duration < 120_000:

                    high_times.append(duration)

                high_start = None

    # --------------------------------------------------------
    # Check for 40 bits
    # --------------------------------------------------------

    if len(high_times) < 40:

        raise RuntimeError(
            f"Incomplete DHT11 response: "
            f"{len(high_times)} bits detected"
        )

    # Use last 40 data pulses
    high_times = high_times[-40:]

    # --------------------------------------------------------
    # Convert pulse widths to bits
    # --------------------------------------------------------

    bits = []

    for duration in high_times:

        if duration > 45_000:
            bits.append(1)
        else:
            bits.append(0)

    # --------------------------------------------------------
    # Convert 40 bits into 5 bytes
    # --------------------------------------------------------

    data = []

    for i in range(5):

        byte = 0

        for bit in bits[i * 8:(i + 1) * 8]:

            byte = (byte << 1) | bit

        data.append(byte)

    # --------------------------------------------------------
    # DHT11 data
    # --------------------------------------------------------

    humidity_int = data[0]
    humidity_decimal = data[1]

    temperature_int = data[2]
    temperature_decimal = data[3]

    checksum = data[4]

    calculated_checksum = (
        data[0]
        + data[1]
        + data[2]
        + data[3]
    ) & 0xFF

    # --------------------------------------------------------
    # Checksum
    # --------------------------------------------------------

    if calculated_checksum != checksum:

        raise RuntimeError(
            f"DHT11 checksum error "
            f"(received {checksum}, "
            f"calculated {calculated_checksum})"
        )

    temperature = (
        temperature_int
        + temperature_decimal / 10.0
    )

    humidity = (
        humidity_int
        + humidity_decimal / 10.0
    )

    return temperature, humidity


# ============================================================
# DHT11 RETRY
# ============================================================

def read_dht11_with_retry(retries=5):

    last_error = None

    for attempt in range(retries):

        try:

            return read_dht11()

        except Exception as error:

            last_error = error

            if attempt < retries - 1:

                time.sleep(0.2)

    raise last_error


# ============================================================
# MAIN
# ============================================================

try:

    setup_lora()

    print()
    print("LoRa + DHT11 transmitter ready")
    print("Frequency : 433 MHz")
    print("Bandwidth : 125 kHz")
    print("SF        : 7")
    print("CR        : 4/5")
    print("CRC       : ON")
    print("Sync Word : 0x12")
    print("DHT GPIO  : GPIO17")
    print()

    print("Sending temperature and humidity...")
    print()

    while True:

        try:

            temperature, humidity = read_dht11_with_retry()

            print(
                f"Temperature: {temperature:.1f} °C"
            )

            print(
                f"Humidity   : {humidity:.1f} %"
            )

            message = (
                f"Temperature:{temperature:.1f}C,"
                f"Humidity:{humidity:.1f}%"
            )

            send_packet(message)

            print(f"Sent: {message}")
            print()

        except Exception as error:

            print(f"DHT read error: {error}")
            print()

        time.sleep(2)


except KeyboardInterrupt:

    print()
    print("Stopping...")


finally:

    try:
        write_register(REG_OP_MODE, 0x80)
    except Exception:
        pass

    spi.close()
