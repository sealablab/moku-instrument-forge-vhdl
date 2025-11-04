"""Progressive CocoTB tests for forge_voltage_5v0_pkg (0-5.0V)."""

import cocotb
from cocotb.triggers import Timer
import os

TEST_LEVEL = os.getenv('TEST_LEVEL', 'P1_BASIC')
TOLERANCE = 0.001


@cocotb.test()
async def test_conversions(dut):
    """P1: Test voltage to digital conversions."""
    await Timer(1, unit='ns')

    # T1: Zero
    dut.test_voltage.value = 0.0
    await Timer(1, unit='ns')
    assert int(dut.digital_result.value) == 0, "0V -> 0x0000"

    # T2: Mid-range
    dut.test_voltage.value = 2.5
    await Timer(1, unit='ns')
    digital = int(dut.digital_result.value)
    assert abs(digital - 16384) < 10, f"2.5V expected ~16384, got {digital}"

    # T3: Maximum
    dut.test_voltage.value = 5.0
    await Timer(1, unit='ns')
    assert int(dut.digital_result.value) == 32767, "5.0V -> 0x7FFF"

    # T4: Reverse
    dut.test_digital.value = 6553
    await Timer(1, unit='ns')
    voltage = float(dut.voltage_result.value)
    assert abs(voltage - 1.0) < TOLERANCE, f"Expected ~1.0V, got {voltage}V"

    print("✓ PASS")
