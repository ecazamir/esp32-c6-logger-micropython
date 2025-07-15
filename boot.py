# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()

import sys, machine, os, vfs, time
import qwiic_i2c, qwiic_max1704x, neopixel
import config

# Display time
rtc = machine.RTC()
MACHINE_Type = os.uname()[4]
NP = None

qwiic_i2c_bus = None
machine_i2c_bus = None
connected_i2c_devices = None
lipo_battery_gauge = None
lipo_alert_pin = None
lipo_alrt_triggered = False


# Initialize the Watchdog Timer
def init_watchdog():
    # Initialize a watchdog timer with a timeout of config.WATCHDOG_TIMEOUT_MS / 1000 seconds
    # This will reset the device if it hangs for more than config.WATCHDOG_TIMEOUT_MS
    # Adjust the timeout as needed for your application
    wdt = machine.WDT(timeout=config.WATCHDOG_TIMEOUT_MS)
    print("Watchdog timer initialized")
    return wdt


def check_sdcard_present(debug=False):
    """
    Checks for the presence of an SD card using the Card Detect (CD) pin.
    Returns True if a card is detected, False otherwise.
    """
    # The SD_Det_Pin on the SparkFun Thing Plus is connected to the CD switch.
    # When a card is inserted, the switch closes and pulls the pin to GND.
    # We configure the pin as an input with a pull-up resistor.
    # A value of 0 means a card is present.
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


def mount_sdcard(debug=False):
    """
    Initializes the SDCard driver and mounts the filesystem.
    This function should only be called after confirming the card is present.
    """
    try:
        sdcard = machine.SDCard(
            sck=machine.Pin(config.SPI_SCK_Pin),
            miso=machine.Pin(config.SPI_MISO_Pin),
            mosi=machine.Pin(config.SPI_MOSI_Pin),
            cs=machine.Pin(config.SPI_CS_Pin),
        )
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


def init_sdcard(debug=False):
    """Checks for and mounts the SD card if present."""
    if check_sdcard_present(debug=debug):
        mount_sdcard(debug=debug)
    elif debug:
        print("SD card not detected via CD pin, skipping mount.")


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


def print_wakeup_reason():
    wakeup_reason = machine.wake_reason()
    reasons = {
        machine.PWRON_RESET: "Power on reset",
        machine.HARD_RESET: "Hard reset",
        machine.WDT_RESET: "Watchdog timer reset",
        machine.DEEPSLEEP_RESET: "Deep sleep reset",
        machine.SOFT_RESET: "Soft reset",
    }
    msg = reasons.get(wakeup_reason, "Unknown reason")


# I2C init
class DeviceInitializer:
    def __init__(self, debug=False):
        self.debug = debug
        self.i2c_known_ids_and_names = {  # Local, not global
            0x32: "RV-8803-based Real time clock module",
            0x36: "MAX1704x-based battery gauge",
            0x38: "AHT20 humidity and temperature sensor",
            0x48: "ADS101x-based ADC",
            0x77: "BMP280 barometric and temperature sensor",
        }
        self.qwiic_i2c_bus = None
        self.machine_i2c_bus = None
        self.connected_i2c_devices = None
        self.lipo_battery_gauge = None
        self.lipo_alert_pin = None
        self.lipo_alrt_triggered = False

    def init_i2c(self):
        # ... (rest of the code)
        # Two objects will be used:
        # - qwiic_i2c, to discuss with resources accessed through SparkFun qwiic hardware
        #   and software ecosystem
        # - machine_i2c, to discuss with resources accessed through the vanilla I2C driver        
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
        # ... (rest of the code)
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


def init_neopixel(success=False):
    global NP
    if MACHINE_Type == "ESP32C6 module with ESP32C6":
        # Expecting a SparkFun ESP32C6 board having a neopixel LED on pin23
        try:
            NP = neopixel.NeoPixel(machine.Pin(config.NP_LED_Pin, machine.Pin.OUT), 1)
            if success:
                NP[0] = (0, 4, 0)  # create a low brightness green light for success
            else:
                NP[0] = (0, 0, 4)  # create a low brightness red light for failure
            NP.write()
        except Exception as e:
            print(f"Error initializing or setting Neopixel: {e}")


# Main boot seq begins here
ctime = rtc.datetime()
print(
    f"Date/time at boot start: {ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d} {ctime[4]:02d}:{ctime[5]:02d}:{ctime[6]:02d}.{ctime[7]:06d}"
)
print(f"Code running on machine type: {MACHINE_Type}")
init_neopixel(False)  # Initialize neopixel and indicate boot start with Blue

print_wakeup_reason()
# wdt = init_watchdog()
try:
    set_cpu_clock()
    init_sdcard(debug=config.DEBUG_MODE)
    device_init_state = DeviceInitializer(debug=config.DEBUG_MODE)
    init_neopixel()
except KeyboardInterrupt:
    print("Interrupted, exiting")
    sys.exit(0)

# Set NeoPixel to Green
NP[0]=(0, 4, 0)
NP.write()

ctime = rtc.datetime()
print(
    f"Date/time at boot end: {ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d} {ctime[4]:02d}:{ctime[5]:02d}:{ctime[6]:02d}.{ctime[7]:06d}"
)
