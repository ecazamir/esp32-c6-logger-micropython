# ESP32-C6 logger designed for SparkFun Thing Plus ESP32-C6

## Purpose

This code is intended to be an application whth the following capabilities:

- [x] Initialize an ESP32-C6 based board (SparkFun Thing Plus ESP32-C6 was used)
- [x] Write data to an SD card
- [ ] Perform various actions on timer event
- [ ] Connect to WiFi network, synchronize module's time with NTP, then sync a hardware clock module (on-demand)
- [ ] Send log samples trough the network, via HTTP request, or MQTT

## Initial setup

### Install micropython on the board

At the time when writing this, the most suitable micropython pre-built package available to [download](https://micropython.org/download/?mcu=esp32c6) is the generic ESP32-C6 package, version 1.25.0. There is no pre-packaged build specifically for SparkFun ESP32C6, which means that all pin mappings should be configured manually. For this purpose, use the [configuration file](./config.py) and customize it for your needs.

A notable mention here is that some sensors/modules developed by SparkFun have micropython libraries which depend entirely on SparkFun's I2C driver qwiic_i2c. For example, I wasn't able to find a library for the RV-8803 real time clock module other than [qwiic_rw8803](https://github.com/sparkfun/qwiic_rv-8803_py), and the library developed by SparkFun for the ADS1015 ADC module (a 12 bit quad channel ADC), which should be able to read voltage from any ADS1115 module, but it also needs some refactoring to use the full 16 bit available on the latter sensor. To avoid that, I had to replace the ADS1015 provided by SparkFun with an ADS1115 library which can operate with all sensors in the ADS1xxx family. Obviously, the latter library doesn't operate with Qwiic_I2C obhects, but with machine.I2C-based ones. That is a small tradeoff in regards to memory, however, the memory available on the SparkFun ESP32-C6 module seems to be enough to handle this small inconvenient.

After downloading the image, put the controller in boot mode and copy the image on the new USB storage device.

## Inventory your sensors

My plan is to use cheap and good enough sensors / modules for:

| Parameter | Description |
|---|----------------------------------------------------------------|
| Temperature | AHT20, BMP280 or any other I2C-based sensor |
| Humidity | AHT20 I2C-based sensor |
| Pressure | BMP280 or any other |
| Real time clock | RV8803-based module |
| Analog voltage | ADS1115-based module |

In addition to the above, the board has:
| Component | Description |
|---|---|
| MAX17048 battery gauge | An I2C connected module which can report on battery voltage, state of charge, and it also can trigger an alert (on GPIO pin 11 on SparhFun Thing Plus ESP32-C6) |
| A NeoPixel RGB led | There's no standard LED to interact with, by simply putting machine.Pin(x).on(). The LED on this board can be controlled as any other NeoPixel LED |

## Install the libraries

For the sensors above, I've been using the following libraries:

| Sensor/component | Library |
|-------|--------------------------------|
| Sparkfun Qwiic I2C library | [Qwiic_I2C_Py](https://github.com/sparkfun/Qwiic_I2C_Py) |
| SparkFun MAX1704x library | [qwiic_max1704x_py](https://github.com/sparkfun/qwiic_max1704x_py) |
| AHT20 (Temperature and humidity) | [micropython_aht0x](https://github.com/targetblank/micropython_ahtx0/tree/master) | 
| BMP280 (Barometric pressure and temperature) | [micropython-bmp280](https://github.com/dafvid/micropython-bmp280/tree/master) |
| Sparkfun RV8803 (Real time clock) | [qwiic_rw8803](https://github.com/sparkfun/qwiic_rv-8803_py) |
| ADS1x15 (Quad channel ADS1x15 based ADC) | [ads1x15](https://github.com/robert-hh/ads1x15) |

I was able to install the sparkfun libraries as described in their READMEs, using `mip remote`. The other single-file libraries usually must be copied to the `/lib` in your module, Thonny IDE can help you do that.

# The real application

In my case, the real deal is about gathering samples from the sensors, adding an accurate timestamp from the RTC, then store the data on the SD card, or through the network.

For this purpose, I've organized the code as followng:

| Item | Purpose | 
|---|---|
| [boot.py](./boot.py) | The script which is executed turing boot-up, as per micropython ways of working |
| [config.py](./config.py) | This file contains the application- and board- specific details, in Python syntax. boot.py pulls it in during boot |
| [main.py](./main.py) | The main script, where the data polling, interrupt handlers, data persistence, sleep etc happens |
