#!/usr/bin/env python3
import json
import os
import sys

from smbus2 import SMBus


INA219_CONFIG = 0x00
INA219_SHUNT_VOLTAGE = 0x01
INA219_BUS_VOLTAGE = 0x02
INA219_CONTINUOUS_32V_320MV = 0x3FFF
DEFAULT_BUSES = (1, 0)
DEFAULT_ADDRESSES = (0x43, 0x42)
EMPTY_VOLTAGE = float(os.environ.get("WAVESHARE_UPS_EMPTY_VOLTAGE", "6.0"))
FULL_VOLTAGE = float(os.environ.get("WAVESHARE_UPS_FULL_VOLTAGE", "8.4"))


def env_ints(name, defaults):
    text = os.environ.get(name, "")
    if not text.strip():
        return defaults

    values = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        values.append(int(item, 0))
    return tuple(values) or defaults


def swap_word(value):
    return ((value & 0xFF) << 8) | (value >> 8)


def read_u16(bus, address, register):
    return swap_word(bus.read_word_data(address, register))


def read_i16(bus, address, register):
    value = read_u16(bus, address, register)
    if value & 0x8000:
        value -= 0x10000
    return value


def voltage_percent(voltage):
    if FULL_VOLTAGE <= EMPTY_VOLTAGE:
        return None
    percent = round((voltage - EMPTY_VOLTAGE) * 100 / (FULL_VOLTAGE - EMPTY_VOLTAGE))
    return max(0, min(100, percent))


def detect_status():
    buses = env_ints("WAVESHARE_UPS_I2C_BUS", DEFAULT_BUSES)
    addresses = env_ints("WAVESHARE_UPS_I2C_ADDRS", DEFAULT_ADDRESSES)

    for bus_number in buses:
        try:
            bus = SMBus(bus_number)
        except OSError:
            continue

        with bus:
            for address in addresses:
                try:
                    bus.write_word_data(address, INA219_CONFIG, swap_word(INA219_CONTINUOUS_32V_320MV))
                    shunt_raw = read_i16(bus, address, INA219_SHUNT_VOLTAGE)
                    bus_raw = read_u16(bus, address, INA219_BUS_VOLTAGE)
                except OSError:
                    continue

                bus_voltage = ((bus_raw >> 3) * 4) / 1000.0
                shunt_voltage = (shunt_raw * 10) / 1_000_000.0
                pack_voltage = bus_voltage + shunt_voltage
                percent = voltage_percent(pack_voltage)
                if percent is not None:
                    return {
                        "percent": percent,
                        "charging": shunt_raw > 0,
                    }
    return None


def main():
    status = detect_status()
    if status is None:
        return 1
    print(json.dumps(status, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
