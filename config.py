# This file is imported by boot.py, therefore it should adhere 
# to python syntax.

# Parameters below are is specific to SparkFun Thing Plus ESP32-C6
# and to the modules used in the build.

MACHINE_FREQ = 100000000    # can be 160 (native), 80 or 40 MHz on ESP32-C6. 133Mhz on rp2/2040
# I2C details
I2C_FREQUENCY = 100000      # Operate i2c at 100 kHz
I2C_SDA_PIN = 6             # I2C SDA: 6 on SparkFun Thing Plus ESP32-C6 and Thing Plus RP2040
I2C_SCL_PIN = 7             # I2C SCL: 7 on SparkFun Thing Plus ESP32-C6 and Thing Plus RP2040
# SD Card related details
SPI_SD_Number = 1           # SPI No. telling where the SD card is attached. 1 for ThingPlus RP2040
SPI_CS_Pin = 9              # SPI CS: 18 on SparkFun Thing Plus ESP32-C6, 9 on Thing Plus RP2040
SPI_MISO_Pin = 21           # SPI MISO: 21 on SparkFun Thing Plus ESP32-C6, 12 on Thing Plus RP2040
SPI_MOSI_Pin = 20           # SPI MOSI: 20 on SparkFun Thing Plus ESP32-C6, 15 on Thing Plus RP2040
SPI_SCK_Pin = 14            # SPI_SCK: 19 on SparkFun Thing Plus ESP32-C6, 14 on Thing Plus RP2040
SD_Det_Pin = None           # SD_Det = SD Detect: 22 on SparkFun Thing Plus ESP32-C6, None on Thing Plus RP2040
SD_Mount_Point = "/sd"
# Neopixel LED details
NP_LED_Pin = 8              # Neopixel LED pin: 23 on SparkFun Thing Plus ESP32-C6, 8 on Thing Plus RP2040
# Battery gauge settings
BATTERY_ALERT_THRESHOLD = 5
BATTERY_ALERT_PIN = 11              # This is wired on SparkFun Thing Plus ESP32-C6 between MAX17048 !ALRT pin and Pin 11
WATCHDOG_TIMEOUT_MS = 30000         # In seconds
DEBUG_MODE = True
LOG_INTERVAL_SECONDS = 5
START_MAIN_DELAY_SECONDS = 5
ADC_CHIP = "ADS1015"                # Valid values: ADS1115 and ADS1015
ADC_GAIN = 1                        # Valid values for full scale measurement: 0:6.144V, 1:4.096V, 2:2.048V, 3:1.024V, 4:0.512V, 5:0.256V
ADC_MULTIPLIERS = (3.62, 1, 1, 1)   # Should be the same as the voltage divider put in front of the respective Ax line of the ADC input
SYS_SLEEP_TYPE = "sleep_ms"         # Valid values: 'sleep_ms' from time package, 'lightsleep' from machine. Use of lightsleep leads to loss of the USB connection while developing.
SYS_SYNC_MAX_DELAY_SECONDS = 60     # Force flush data to the SD card if last sync is older than this number of seconds
