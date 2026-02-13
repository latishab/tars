#!/usr/bin/env python3
"""Test hybrid battery module functionality."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

from modules.module_battery import BatteryModule, VOLTAGE_TO_SOC_3S

# Test voltage_to_soc interpolation
print("=" * 60)
print("Testing voltage_to_soc() interpolation:")
print("=" * 60)

battery = BatteryModule(auto_shutdown=False)

test_voltages = [
    12.60,  # 100%
    12.52,  # Between 12.60 and 12.45
    12.00,  # 80%
    11.55,  # Between entries
    10.50,  # 30%
    10.00,  # 0%
    9.50,   # Below cutoff
]

for voltage in test_voltages:
    soc = battery.voltage_to_soc(voltage)
    mAh = battery._voltage_to_mAh(voltage)
    print(f"Voltage: {voltage:.2f}V → SoC: {soc:.1f}% → {mAh:.0f}mAh")

print("\n" + "=" * 60)
print("Testing battery state:")
print("=" * 60)

if battery.sensor_initialized:
    # Read current state
    status = battery.get_battery_status()
    print(f"Current voltage:    {status['voltage']:.3f}V")
    print(f"Current:            {status['current']:+.0f}mA")
    print(f"Power:              {status['power']:.1f}mW")
    print(f"Remaining:          {status['remaining_mAh']:.0f}mAh")
    print(f"Percentage:         {status['normalized_percentage']}%")
    
    # Test voltage lookup for current voltage
    voltage_soc = battery.voltage_to_soc(status['voltage'])
    print(f"\nVoltage-based SoC:  {voltage_soc:.1f}%")
else:
    print("Battery sensor not initialized")

print("\n" + "=" * 60)
print("Lookup table:")
print("=" * 60)
for voltage, soc in VOLTAGE_TO_SOC_3S:
    print(f"{voltage:.2f}V → {soc:3d}%")
