# This file is imported by boot.py, therefore it should adhere 
# to python syntax.

# Parameters below are is specific to SparkFun Thing Plus ESP32-C6
# And to the modules used in the build.
MACHINE_FREQ = 160000000    # can be 160 (native), 80 or 40 MHz on ESP32-C6
# I2C details
I2C_FREQUENCY = 100000      # Operate i2c at 100 kHz
I2C_SDA_PIN = 6
I2C_SCL_PIN = 7
# SD Card related details
SPI_CS_Pin = 18
SPI_MISO_Pin = 21
SPI_MOSI_Pin = 20
SPI_SCK_Pin = 19
SD_Det_Pin = 22
SD_Mount_Point = "/sd"
# Neopixel LED details
NP_LED_Pin = 23
# Battery gauge settings
BATTERY_ALERT_THRESHOLD = 5
BATTERY_ALERT_PIN = 11          # This is wired on SparkFun Thing Plus ESP32-C6 between MAX17048 !ALRT pin and Pin 11
WATCHDOG_TIMEOUT_MS = 30000     # In seconds
DEBUG_MODE = True
LOG_INTERVAL_SECONDS = 5
START_MAIN_DELAY_SECONDS = 5
ADC_CHIP = "ADS1015"                # Valid values: ADS1115 and ADS1015
ADC_GAIN = 2                        # Valid values for full scale measurement: 0:6.144V, 1:4.096V, 2:2.048V, 3:1.024V, 4:0.512V, 5:0.256V
SYS_SLEEP_TYPE = 'sleep_ms'	        # Valid values: 'sleep_ms' from time package, 'lightsleep' from machine. Use of lightsleep leads to loss of the USB connection while developing.
SYS_SYNC_MAX_DELAY_SECONDS = 120    # Force flush data to the SD card if last sync is older than this amount of seconds
