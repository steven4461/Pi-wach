# Pico 2 W Local Temperature Page

The Pico joins your existing 2.4 GHz Wi-Fi network and serves the live sensor page at its local network address. No cloud service or separate web server is used.

## Setup

UF2 is the CircuitPython firmware, not a compiled version of this Python application. Install the CircuitPython UF2 for Raspberry Pi Pico 2 W once: hold `BOOTSEL` while plugging in the board, then copy the downloaded UF2 onto the `RPI-RP2` drive. The board reboots with a `CIRCUITPY` drive.

Build a board-ready ZIP on your computer:

```sh
python build.py
```

Enter your Wi-Fi name and password when prompted. The password is hidden while typing. The script creates `dist/pico2w-circuitpython.zip`, containing the app, sensor registry, `index.html`, and generated `secrets.py`. It also includes drivers placed in the project's `lib/` folder. The ZIP contains your Wi-Fi password; keep it private. Extract its files to the root of the board's `CIRCUITPY` drive. The generated ZIP and live `secrets.py` are ignored by Git.

Connect your phone or computer to the same Wi-Fi network. Open the CircuitPython serial console; when the Pico connects, it prints its local IP address. Open that address in your browser.

The onboard reading is the processor's temperature, not room temperature. The page also reports the Pico's VSYS input voltage and CPU frequency.

## Optional sensors

The Pico has one shared I2C bus. Connect compatible modules in parallel to 3V3, GND, GP0/SDA, and GP1/SCL. Enable the sensor by changing its `False` entry to `True` in `SENSOR_CONFIG` in `sensors.py`. Only enable sensors you have connected. The registry supports:

- BME280: temperature, humidity, pressure
- SHT31D: temperature, humidity
- BMP280: temperature, pressure
- BH1750 and TSL2591: visible light level
- LTR390: light level and UV sensor counts
- SGP30: equivalent CO2 and total volatile organic compounds
- MPU6050: 3-axis acceleration, rotation, and sensor temperature
- INA219: bus voltage, current, and power
- MCP9808: temperature

Install drivers for the sensors you enabled with `circup install adafruit_bme280 adafruit_sht31d adafruit_bmp280 adafruit_bh1750 adafruit_tsl2591 adafruit_ltr390 adafruit_sgp30 adafruit_mpu6050 adafruit_ina219 adafruit_mcp9808` while the board is connected. `circup` installs their dependencies too. To put drivers in the build ZIP, copy `CIRCUITPY/lib` into the project as `lib/` before running `build.py`. Sensors are detected by I2C address at startup; check the serial console for setup messages. BME280 and BMP280 modules commonly share an I2C address, so use one of those at a time.

### Analog sensors

The `ANALOG_CHANNELS` map in `sensors.py` supports analog-output sensors. Add names and pins such as `"Soil moisture": board.A1` or `"Light level": board.A2`; these are reported as raw voltage and need sensor-specific calibration. For TMP36, use `"TMP36 ambient temperature": (board.A0, "tmp36")` to get converted Celsius and Fahrenheit readings. Connect analog output to the configured pin and power/GND appropriately; never let an input exceed 3.3 V.

More modules can be added by extending `SENSOR_DRIVERS` and `read_sensors()` in `sensors.py`; install their CircuitPython drivers into `lib/` for the builder to package them.