import analogio
import board


SENSOR_CONFIG = {
    "BME280": False,
    "SHT31D": False,
    "BMP280": False,
    "BH1750": False,
    "TSL2591": False,
    "LTR390": False,
    "SGP30": False,
    "MPU6050": False,
    "INA219": False,
    "MCP9808": False,
}

ANALOG_CHANNELS = {
    # Example: "TMP36 ambient temperature": (board.A0, "tmp36"),
    # Example: "Soil moisture": board.A1,
    # Example: "Light level": board.A2,
}

SENSOR_DRIVERS = {
    "BME280": ("adafruit_bme280", "Adafruit_BME280_I2C", (0x76, 0x77)),
    "SHT31D": ("adafruit_sht31d", "SHT31D", (0x44, 0x45)),
    "BMP280": ("adafruit_bmp280", "Adafruit_BMP280_I2C", (0x76, 0x77)),
    "BH1750": ("adafruit_bh1750", "BH1750", (0x23, 0x5C)),
    "TSL2591": ("adafruit_tsl2591", "TSL2591", (0x29,)),
    "LTR390": ("adafruit_ltr390", "LTR390", (0x53,)),
    "SGP30": ("adafruit_sgp30", "Adafruit_SGP30", (0x58,)),
    "MPU6050": ("adafruit_mpu6050", "MPU6050", (0x68, 0x69)),
    "INA219": ("adafruit_ina219", "INA219", (0x40,)),
    "MCP9808": ("adafruit_mcp9808", "MCP9808", (0x18,)),
}


def initialize_sensors():
    enabled = [name for name, active in SENSOR_CONFIG.items() if active]
    sensors = {}
    analog_sensors = []

    for name, config in ANALOG_CHANNELS.items():
        if isinstance(config, tuple):
            pin, sensor_type = config
        else:
            pin, sensor_type = config, "voltage"
        try:
            analog_sensors.append((name, analogio.AnalogIn(pin), sensor_type))
        except Exception as error:
            print("Analog sensor setup failed:", name, error)

    if not enabled:
        return sensors, analog_sensors

    i2c = board.I2C()
    while not i2c.try_lock():
        pass
    try:
        addresses = i2c.scan()
    finally:
        i2c.unlock()

    claimed_addresses = set()
    for name in enabled:
        module_name, class_name, supported_addresses = SENSOR_DRIVERS[name]
        address = next(
            (candidate for candidate in supported_addresses
             if candidate in addresses and candidate not in claimed_addresses),
            None,
        )
        if address is None:
            print(name, "not detected on I2C")
            continue

        try:
            module = __import__(module_name)
            driver_class = getattr(module, class_name)
            if name in ("BME280", "SHT31D", "BMP280", "BH1750"):
                sensor = driver_class(i2c, address=address)
            else:
                sensor = driver_class(i2c)
            if name == "SGP30":
                sensor.iaq_init()
            sensors[name] = sensor
            claimed_addresses.add(address)
            print(name, "detected at 0x%02X" % address)
        except Exception as error:
            print(name, "setup failed:", error)

    return sensors, analog_sensors


def read_sensors(sensors, analog_sensors):
    readings = []

    for name, analog_input, sensor_type in analog_sensors:
        try:
            volts = analog_input.value * 3.3 / 65535
            if sensor_type == "tmp36":
                celsius = (volts - 0.5) * 100
                fahrenheit = celsius * 9 / 5 + 32
                value = "%.1f C / %.1f F" % (celsius, fahrenheit)
            else:
                value = "%.3f V" % volts
            readings.append({"sensor": name, "reading": value})
        except OSError as error:
            print(name, "read error:", error)

    for name, sensor in sensors.items():
        try:
            if name == "BME280":
                readings.extend((
                    {"sensor": "BME280 temperature", "reading": "%.1f C" % sensor.temperature},
                    {"sensor": "BME280 humidity", "reading": "%.1f %%" % sensor.relative_humidity},
                    {"sensor": "BME280 pressure", "reading": "%.1f hPa" % sensor.pressure},
                ))
            elif name == "SHT31D":
                readings.extend((
                    {"sensor": "SHT31D temperature", "reading": "%.1f C" % sensor.temperature},
                    {"sensor": "SHT31D humidity", "reading": "%.1f %%" % sensor.relative_humidity},
                ))
            elif name == "BMP280":
                readings.extend((
                    {"sensor": "BMP280 temperature", "reading": "%.1f C" % sensor.temperature},
                    {"sensor": "BMP280 pressure", "reading": "%.1f hPa" % sensor.pressure},
                ))
            elif name == "BH1750":
                readings.append({"sensor": "BH1750 light", "reading": "%.1f lux" % sensor.lux})
            elif name == "TSL2591":
                readings.append({"sensor": "TSL2591 light", "reading": "%.1f lux" % sensor.lux})
            elif name == "LTR390":
                readings.extend((
                    {"sensor": "LTR390 light", "reading": "%.1f lux" % sensor.lux},
                    {"sensor": "LTR390 UV counts", "reading": "%d" % sensor.uvs},
                ))
            elif name == "SGP30":
                eco2, tvoc = sensor.iaq_measure()
                readings.extend((
                    {"sensor": "SGP30 equivalent CO2", "reading": "%d ppm" % eco2},
                    {"sensor": "SGP30 VOC", "reading": "%d ppb" % tvoc},
                ))
            elif name == "MPU6050":
                acceleration = sensor.acceleration
                gyro = sensor.gyro
                readings.extend((
                    {"sensor": "MPU6050 acceleration", "reading": "%.2f, %.2f, %.2f m/s2" % acceleration},
                    {"sensor": "MPU6050 rotation", "reading": "%.2f, %.2f, %.2f rad/s" % gyro},
                    {"sensor": "MPU6050 temperature", "reading": "%.1f C" % sensor.temperature},
                ))
            elif name == "INA219":
                readings.extend((
                    {"sensor": "INA219 bus voltage", "reading": "%.2f V" % sensor.bus_voltage},
                    {"sensor": "INA219 current", "reading": "%.2f mA" % sensor.current},
                    {"sensor": "INA219 power", "reading": "%.2f mW" % sensor.power},
                ))
            elif name == "MCP9808":
                readings.append({"sensor": "MCP9808 temperature", "reading": "%.1f C" % sensor.temperature})
        except Exception as error:
            print(name, "read error:", error)
            readings.append({"sensor": name, "reading": "Read error"})

    return readings