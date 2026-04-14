#!/usr/bin/env python3
import json
import os
import sys
import time

try:
    from smbus2 import SMBus
except Exception:
    SMBus = None


INA219_CONFIG = 0x00
INA219_SHUNT_VOLTAGE = 0x01
INA219_BUS_VOLTAGE = 0x02
INA219_CONTINUOUS_32V_320MV = 0x3FFF
DEFAULT_BUSES = (1, 0)
DEFAULT_ADDRESSES = (0x43, 0x42)
EMPTY_VOLTAGE = float(os.environ.get("WAVESHARE_UPS_EMPTY_VOLTAGE", "6.0"))
FULL_VOLTAGE = float(os.environ.get("WAVESHARE_UPS_FULL_VOLTAGE", "8.4"))
DEFAULT_RETRIES = max(1, int(os.environ.get("WAVESHARE_UPS_RETRIES", "2")))
RETRY_DELAY_SEC = max(0.0, float(os.environ.get("WAVESHARE_UPS_RETRY_DELAY_SEC", "0.2")))


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


def ordered_unique(values):
    ordered = []
    seen = set()
    for value in values:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def available_i2c_buses():
    discovered = []

    dev_root = "/dev"
    if os.path.isdir(dev_root):
        for name in os.listdir(dev_root):
            if not name.startswith("i2c-"):
                continue
            try:
                discovered.append(int(name.split("-", 1)[1]))
            except ValueError:
                continue

    sys_root = "/sys/class/i2c-dev"
    if os.path.isdir(sys_root):
        for name in os.listdir(sys_root):
            if not name.startswith("i2c-"):
                continue
            try:
                discovered.append(int(name.split("-", 1)[1]))
            except ValueError:
                continue

    return ordered_unique(sorted(discovered))


def candidate_buses():
    configured = env_ints("WAVESHARE_UPS_I2C_BUS", ())
    if configured:
        return configured
    return ordered_unique((*DEFAULT_BUSES, *available_i2c_buses())) or DEFAULT_BUSES


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


def detect_status_once():
    if SMBus is None:
        return None

    buses = candidate_buses()
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


def detect_status():
    attempts = DEFAULT_RETRIES
    for attempt in range(attempts):
        status = detect_status_once()
        if status is not None:
            return status
        if attempt + 1 < attempts:
            time.sleep(RETRY_DELAY_SEC)
    return None


def main():
    status = detect_status()
    if status is None:
        return 1
    print(json.dumps(status, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
