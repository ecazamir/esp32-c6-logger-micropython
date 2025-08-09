# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()

import sys, machine, os, vfs, time
import qwiic_i2c, qwiic_max1704x, neopixel, ads1x15, qwiic_rv8803
import config

# Display time
rtc = machine.RTC()
MACHINE_Type = os.uname()[4]

# Initialize the Watchdog Timer
def init_watchdog():
    # Initialize a watchdog timer with a timeout of config.WATCHDOG_TIMEOUT_MS / 1000 seconds
    # This will reset the device if it hangs for more than config.WATCHDOG_TIMEOUT_MS
    # Adjust the timeout as needed for your application
    wdt = machine.WDT(timeout=config.WATCHDOG_TIMEOUT_MS)
    print("Watchdog timer initialized")
    return wdt

def set_cpu_clock():
    current_freq = machine.freq()
    if current_freq != config.MACHINE_FREQ:
        try:
            print(
                f"Setting machine timer to {config.MACHINE_FREQ} instead of {machine.freq()}"
            )
            machine.freq(config.MACHINE_FREQ)
        except Exception as e:
            print("An error occurred while setting CPU frequency:", e)
    else:
        print(f"Controller clock is {(current_freq / 1000000)} MHz")


def print_wakeup_reason(debug=False):
    # This applies to ESP-based hardware, RP2040 can't do that.
    if (MACHINE_Type in ('ESP32C6 module with ESP32C6')):
        wakeup_reason = machine.wake_reason()
        reasons = {
            machine.PWRON_RESET: "Power on reset",
            machine.HARD_RESET: "Hard reset",
            machine.WDT_RESET: "Watchdog timer reset",
            machine.DEEPSLEEP_RESET: "Deep sleep reset",
            machine.SOFT_RESET: "Soft reset",
        }
        msg = reasons.get(wakeup_reason, "Unknown reason")
    else:
        msg = f'Unknown wakeup reason (code running on "{MACHINE_Type}")'
    if (config.DEBUG_MODE):
        print(msg)


# I2C init
class LoggingPlatform:
    def __init__(self, debug=False):
        self.debug = debug
        self.i2c_known_ids_and_names = {  # Local, not global
            0x32: "RV-8803-based Real time clock module",
            0x36: "MAX1704x-based battery gauge",
            0x38: "AHT20 humidity and temperature sensor",
            0x48: "ADS1x15-based ADC",
            0x77: "BMP280 barometric and temperature sensor",
        }
        self.qwiic_i2c_bus = None
        self.machine_i2c_bus = None
        self.connected_i2c_devices = None
        self.lipo_battery_gauge = None
        self.lipo_alert_pin = None
        self.ads_1x15 = None
        self.rtc_module = None
        self.neopixel = None
        self.init_neopixel()

    def init_i2c(self):
        # ... (rest of the code)
        # Two objects will be used:
        # - qwiic_i2c, to communicate with modules accessed through the SparkFun qwiic_i2c library
        #   and software ecosystem
        # - machine_i2c, to communicate with modules accessed through the vanilla I2C driver        
        try:
            self.qwiic_i2c_bus = qwiic_i2c.get_i2c_driver(
                sda=config.I2C_SDA_PIN, scl=config.I2C_SCL_PIN, freq=config.I2C_FREQUENCY
            )
            self.machine_i2c_bus = machine.I2C(
                sda=machine.Pin(config.I2C_SDA_PIN), scl=machine.Pin(config.I2C_SCL_PIN)
            )
            self.connected_i2c_devices = self.qwiic_i2c_bus.scan()
            # Do a ping on the bus, against all discovered devices
            # Using the qwiic_i2c object/class
            if self.debug:
                print("I2C scan:")
                for device_address in self.connected_i2c_devices:
                    ping_result = self.qwiic_i2c_bus.ping(device_address)
                    print(
                        f"  - 0x{device_address:02x}: {self.i2c_known_ids_and_names.get(device_address, 'Unknown')}"
                    )  # Use .get() for safety
        except Exception as e:
            print(f"Exception occurred while scanning for I2C devices: {e}")  # More informative message
            # Consider re-raising or returning an error code if needed
            return False
        return True

    def init_lipo(self):
        if 0x36 in self.connected_i2c_devices:
            if self.debug:
                print("Initializing battery gauge at I2c:0x36")
            try:
                self.lipo_battery_gauge = qwiic_max1704x.QwiicMAX1704X(
                    qwiic_max1704x.QwiicMAX1704X.kDeviceTypeMAX17048,
                    i2c_driver=self.qwiic_i2c_bus,
                )
                self.lipo_battery_gauge.begin()
                self.lipo_battery_gauge.set_threshold(config.BATTERY_ALERT_THRESHOLD)
                # Get first reading
                batt_voltage = self.lipo_battery_gauge.get_voltage()
                batt_soc = self.lipo_battery_gauge.get_soc()
                if self.debug:
                    batt_alert_flag = self.lipo_battery_gauge.get_alert()
                    batt_chg_rate = self.lipo_battery_gauge.get_change_rate()
                    print(
                        f"  Battery reading: {batt_voltage:.2f}V, {batt_soc:.2f}% SOC, ChgRate: {batt_chg_rate}, Alert flag: {batt_alert_flag}"
                    )
                else:
                     print(f"  Battery reading: {batt_voltage:.2f}V, {batt_soc:.2f}% SOC")
                # Get !ALRT value via config.BATTERY_ALERT_PIN
                # Initialize the pin
                self.lipo_alert_pin = machine.Pin(
                    config.BATTERY_ALERT_PIN, machine.Pin.IN
                )  # don't set pull-up, there's one soldered on the board
                if self.debug:
                    print(
                        f"LiPo battery gauge !ALRT pin ({config.BATTERY_ALERT_PIN}): {self.lipo_alert_pin.value()}"
                    )
            except Exception as e:
                print(f"Exception during LiPo initialization/reading: {e}")
                return False  # Indicate failure
        return True

    def init_ads_1x15(self):
        # ... (rest of the code)
        if 0x48 in self.connected_i2c_devices:
            if self.debug:
                print(f"Initializing ADS1x15 at I2c:0x48 with chip type {config.ADC_CHIP} and gain {config.ADC_GAIN}")
            try:
                if config.ADC_CHIP == 'ADS1115':
                    self.ads_1x15 = ads1x15.ADS1115(self.machine_i2c_bus, address=0x48, gain=config.ADC_GAIN)
                elif config.ADC_CHIP == 'ADS1015':
                    self.ads_1x15 = ads1x15.ADS1015(self.machine_i2c_bus, address=0x48, gain=config.ADC_GAIN)
            except Exception as e:
                print(f"Exception during ADC ADS1x15 initialization/reading: {e}")
                return False  # Indicate failure
        else:
            if self.debug:
                print("No ADS1x15 found, skipping ADC initialization")
        return True
    
    def init_rtc(self):
        if 0x32 in self.connected_i2c_devices:
            if self.debug:
                print("Initializing RV8803 RTC module at I2c:0x32")
            self.rtc_module = qwiic_rv8803.QwiicRV8803(address=0x32, i2c_driver=self.qwiic_i2c_bus)
            self.rtc_module.begin()
            self.rtc_module.set_24_hour()
            self.rtc_module.update_time()
            print(f"RTC(RV8803) Date and time: {self.rtc_module.string_time_8601()}")
        else:
            if self.debug:
                print("There's no hardware clock module attached.. Skipping RV8803 RTC module initialization")

    def sync_clock_from_rtc_module(self):
        if self.debug:
                print("Synchronizing controller time from RTC...")
        if self.rtc_module is not None:
            self.rtc_module.update_time()
            mach_rtc = machine.RTC()
            mach_rtc.datetime((
                self.rtc_module.get_year(),
                self.rtc_module.get_month(),
                self.rtc_module.get_date(),
                self.rtc_module.get_weekday(),
                self.rtc_module.get_hours(),
                self.rtc_module.get_minutes(),
                self.rtc_module.get_seconds(),
                self.rtc_module.get_hundredths() * 1000,
            ))
            if self.debug:
                mdt = mach_rtc.datetime()
                print(f"RTC clock set to {mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}T{mdt[4]:02d}:{mdt[5]:02d}:{mdt[6]:02d} from RTC module ")
        else:
            print("The hardware RTC module is not attached, not synchronizing controller time from RTC...")
    
    def get_ads_1x15_voltage_single(self, channel):
        # Rate = 0: 128 samples/second.
        # See all rates here: https://github.com/robert-hh/ads1x15/blob/c2b986bb26f1aed3df7b94f11d30080c103fed1f/ads1x15.py#L117-L126
        return self.ads_1x15.raw_to_v(self.ads_1x15.read(rate=0, channel1=channel))

    def check_sdcard_present(self, debug=False):
        """
        Checks for the presence of an SD card using the Card Detect (CD) pin, if the platform has one.
        Returns True if the platform has a SD Detect pin and a card is detected, False otherwise.
        """
        # The SD_Det_Pin on the SparkFun Thing Plus is connected to the CD switch.
        # When a card is inserted, the switch closes and pulls the pin to GND.
        # We configure the pin as an input with a pull-up resistor.
        # A value of 0 means a card is present.
        if (config.SD_Det_Pin == None):
            return True
        try:
            sd_detect_pin = machine.Pin(
                config.SD_Det_Pin, machine.Pin.IN, machine.Pin.PULL_UP
            )
            # A small delay can help debounce the mechanical switch in the SD card holder
            time.sleep_ms(10)
            is_present = sd_detect_pin.value() == 0
            if debug:
                print(
                    f"SD card detect pin ({config.SD_Det_Pin}) value: {sd_detect_pin.value()}. Card present: {is_present}"
                )
            return is_present
        except Exception as e:
            print(f"Error checking SD card presence on pin {config.SD_Det_Pin}: {e}")
            # If we can't check the pin, it's safer to assume no card is present
            return False

    def mount_sdcard(self, debug=False):
        """
        Initializes the SDCard driver and mounts the filesystem.
        This function should only be called after confirming the card is present.
        """
        try:
            # Do this hardware dependent. Start with the generic ESP32-C6
            if (MACHINE_Type == 'ESP32C6 module with ESP32C6'):
                sdcard = machine.SDCard(
                    sck=machine.Pin(config.SPI_SCK_Pin),
                    miso=machine.Pin(config.SPI_MISO_Pin),
                    mosi=machine.Pin(config.SPI_MOSI_Pin),
                    cs=machine.Pin(config.SPI_CS_Pin),
                )
            elif (MACHINE_Type == 'SparkFun Thing Plus RP2040 with RP2040'):
                # The code below may be applicable to machines having os.uname(sysname) == rp2 as well.
                # This doesn't use machine.SDCard, but sdcard.SDCard, which has different parameters.
                spi1 = machine.SPI(config.SPI_SD_Number)
                import sdcard
                sdcard = sdcard.SDCard(spi1, machine.Pin(config.SPI_CS_Pin))
            if debug:
                print(f"Attempting to mount SD card at {config.SD_Mount_Point}...")
            vfs.mount(sdcard, config.SD_Mount_Point)
            if debug:
                print(f"SD card mounted successfully at {config.SD_Mount_Point}")
            return True
        except OSError as e:
            print(
                f"Error mounting SD card at {config.SD_Mount_Point}. Card may be unformatted or failing initialization. Error: {e}"
            )
        except Exception as e:
            print(
                f"An unexpected error occurred while mounting the SD card at {config.SD_Mount_Point}: {e}"
            )
        return False

    def init_sdcard(self, debug=False):
        """Checks for and mounts the SD card if present."""
        if self.check_sdcard_present(debug=debug):
            self.mount_sdcard(debug=debug)
        elif debug:
            print("SD card not detected via CD pin, skipping mount.")

    def init_neopixel(self):
        if MACHINE_Type in ["ESP32C6 module with ESP32C6","SparkFun Thing Plus RP2040 with RP2040"]:
            # Expecting a SparkFun ESP32C6 board having a neopixel LED on pin23
            try:
                self.neopixel = neopixel.NeoPixel(machine.Pin(config.NP_LED_Pin, machine.Pin.OUT), 1)
                self.neopixel.write()
            except Exception as e:
                print(f"Error initializing or setting Neopixel: {e}")
        else:
            print(f"NeoPixel code was not written for this platform: {MACHINE_Type}")
            self.neopixel = None

    def set_neopixel_rgb(self, r, g, b):
        if self.neopixel:
            self.neopixel[0] = (r, g, b)
            self.neopixel.write()

    def init_devices(self):
        self.init_i2c()
        self.init_lipo()
        self.init_rtc()
        self.sync_clock_from_rtc_module()
        self.init_ads_1x15()
        self.init_sdcard()


# Main boot seq begins here
ctime = rtc.datetime()
print(
    f"Date/time at boot start: {ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d} {ctime[4]:02d}:{ctime[5]:02d}:{ctime[6]:02d}.{ctime[7]:06d}"
)
print(f"Code running on machine type: {MACHINE_Type}")
print_wakeup_reason()

# wdt = init_watchdog()
try:
    set_cpu_clock()
    logging_platform = LoggingPlatform(debug=config.DEBUG_MODE)
    if logging_platform:
        logging_platform.set_neopixel_rgb(0, 0, 4) # Indicate boot start with blue if successful
        logging_platform.init_devices()
        logging_platform.set_neopixel_rgb(0, 4, 0) # Indicate device init success with green
except KeyboardInterrupt:
    logging_platform.set_neopixel_rgb(4, 0, 0) # Set to red = failure
    print("Interrupted, exiting")
    sys.exit(0)
