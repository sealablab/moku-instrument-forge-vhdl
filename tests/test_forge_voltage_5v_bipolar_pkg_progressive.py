"""Progressive CocoTB tests for forge_voltage_5v_bipolar_pkg (±5.0V)."""

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

    # T2: Positive
    dut.test_voltage.value = 3.0
    await Timer(1, unit='ns')
    digital = int(dut.digital_result.value)
    assert abs(digital - 19660) < 10, f"3.0V expected ~19660, got {digital}"

    # T3: Negative
    dut.test_voltage.value = -3.0
    await Timer(1, unit='ns')
    digital = int(dut.digital_result.value.signed_integer)
    assert abs(digital - (-19660)) < 10, f"-3.0V expected ~-19660, got {digital}"

    # T4: Reverse
    dut.test_digital.value = 6553
    await Timer(1, unit='ns')
    voltage = float(dut.voltage_result.value)
    assert abs(voltage - 1.0) < TOLERANCE, f"Expected ~1.0V, got {voltage}V"

    print("✓ PASS")
