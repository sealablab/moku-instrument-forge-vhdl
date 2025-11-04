# Phase 4 Continuation Prompt

**Use this prompt in a fresh Claude Code session from INSIDE the forge-vhdl submodule.**

---

## Context Setup

```
You are working inside the forge-vhdl git submodule located at:
/Users/johnycsh/TTOP/moku-instrument-forge-mono-repo/libs/forge-vhdl

This is a standalone VHDL utilities library with CocoTB progressive testing infrastructure.

Current branch: 20251104-vhdl-forge-dev
Git status: Submodule with clean working tree (post v2.0.0 release)
```

---

## Your Task: Complete Phase 4 - Voltage Type System Implementation

**Status:** ~40% complete (design + test wrappers done, VHDL packages pending)

### What's Already Done ✅

1. **Design finalized** - See `.migration/VOLTAGE_TYPE_SYSTEM_DESIGN.md`
2. **Python reference implementation** - See `.migration/voltage_types_reference.py`
3. **Test wrappers created** - All 3 wrappers exist in `tests/`:
   - `forge_voltage_3v3_pkg_tb_wrapper.vhd`
   - `forge_voltage_5v0_pkg_tb_wrapper.vhd`
   - `forge_voltage_5v_bipolar_pkg_tb_wrapper.vhd`
4. **CocoTB interface rules documented** - In `CLAUDE.md` Section 4
5. **Documentation structure complete** - 3-tier system (llms.txt, CLAUDE.md, specialized docs)

### What You Need To Do ❌

**Phase 4a: Implement VHDL Packages** (~2-3 hours)

Create three VHDL packages in `vhdl/packages/`:

1. **forge_voltage_3v3_pkg.vhd** (0-3.3V unipolar domain)
   - Constants: V_MIN=0.0, V_MAX=3.3, SCALE_FACTOR
   - Reference voltages: 1V, 2.5V, 3.3V (as digital values)
   - Functions:
     - `to_digital(voltage: real) return signed(15 downto 0)`
     - `from_digital(digital: signed(15 downto 0)) return real`
     - `is_valid(voltage: real) return boolean`
     - `clamp(voltage: real) return real`
     - `is_voltage_equal(v1, v2: real; tolerance: real := 0.01) return boolean`

2. **forge_voltage_5v0_pkg.vhd** (0-5.0V unipolar domain)
   - Same structure, scaled for 0-5V range

3. **forge_voltage_5v_bipolar_pkg.vhd** (±5.0V bipolar domain)
   - Same structure, scaled for ±5V range

**Template Pattern (use existing volo_voltage_pkg.vhd as reference):**

```vhdl
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package forge_voltage_3v3_pkg is
    -- Domain constants
    constant V_MIN : real := 0.0;
    constant V_MAX : real := 3.3;
    constant SCALE_FACTOR : real := 32767.0 / V_MAX;  -- Scale to signed(15:0)

    -- Common reference voltages (as digital values)
    constant V_1V0_DIGITAL : signed(15 downto 0) := to_signed(9930, 16);   -- 1.0V
    constant V_2V5_DIGITAL : signed(15 downto 0) := to_signed(24824, 16);  -- 2.5V
    constant V_3V3_DIGITAL : signed(15 downto 0) := to_signed(32767, 16);  -- 3.3V

    -- Conversion functions
    function to_digital(voltage : real) return signed;
    function from_digital(digital : signed(15 downto 0)) return real;

    -- Validation functions
    function is_valid(voltage : real) return boolean;
    function clamp(voltage : real) return real;

    -- Testbench helper
    function is_voltage_equal(v1 : real; v2 : real; tolerance : real := 0.01) return boolean;
end package forge_voltage_3v3_pkg;

package body forge_voltage_3v3_pkg is
    function to_digital(voltage : real) return signed is
        variable clamped : real;
        variable normalized : real;
    begin
        clamped := clamp(voltage);
        normalized := clamped / V_MAX;
        return to_signed(integer(normalized * 32767.0), 16);
    end function;

    function from_digital(digital : signed(15 downto 0)) return real is
        variable int_val : integer;
    begin
        int_val := to_integer(digital);
        return (real(int_val) / 32767.0) * V_MAX;
    end function;

    function is_valid(voltage : real) return boolean is
    begin
        return voltage >= V_MIN and voltage <= V_MAX;
    end function;

    function clamp(voltage : real) return real is
    begin
        if voltage < V_MIN then
            return V_MIN;
        elsif voltage > V_MAX then
            return V_MAX;
        else
            return voltage;
        end if;
    end function;

    function is_voltage_equal(v1 : real; v2 : real; tolerance : real := 0.01) return boolean is
    begin
        return abs(v1 - v2) <= tolerance;
    end function;
end package body forge_voltage_3v3_pkg;
```

**Phase 4b: Create CocoTB Tests** (~2-3 hours)

Create progressive tests in `tests/`:

1. **test_forge_voltage_3v3_pkg_progressive.py**
   - P1 tests (3-4 tests):
     - T1: to_digital() accuracy (0V, 1.65V, 3.3V)
     - T2: from_digital() round-trip
     - T3: is_valid() boundary checks
     - T4: clamp() behavior
   - P2 tests (5-7 tests):
     - Edge cases, precision tests, tolerance tests

2. **test_forge_voltage_5v0_pkg_progressive.py** (similar structure)

3. **test_forge_voltage_5v_bipolar_pkg_progressive.py** (similar structure)

**Test Pattern (use test_volo_lut_pkg_progressive.py as reference):**

```python
import cocotb
from cocotb.triggers import Timer
from test_base import TestBase
import os

class ForgeVoltage3V3Tests(TestBase):
    """Progressive tests for forge_voltage_3v3_pkg"""

    async def run_p1_basic(self):
        """P1: Basic conversion tests (3-4 tests)"""
        await self.test("to_digital accuracy", self.test_to_digital_accuracy)
        await self.test("from_digital round-trip", self.test_from_digital)
        await self.test("is_valid boundary", self.test_is_valid)
        await self.test("clamp behavior", self.test_clamp)

    async def test_to_digital_accuracy(self):
        """Test to_digital() conversion accuracy"""
        # Set test_voltage_digital to 0V (0x0000)
        self.dut.test_voltage_digital.value = 0
        self.dut.sel_to_digital.value = 1
        await Timer(1, units='ns')

        result = int(self.dut.digital_result.value.signed_integer)
        assert result == 0, f"0V should be 0, got {result}"

        # Test 3.3V (0x7FFF = 32767)
        self.dut.test_voltage_digital.value = 32767
        await Timer(1, units='ns')
        result = int(self.dut.digital_result.value.signed_integer)
        assert result == 32767, f"3.3V should be 32767, got {result}"

    async def test_from_digital(self):
        """Test from_digital() round-trip conversion"""
        # ... implementation ...

    # ... more tests ...

# Test instantiation
@cocotb.test()
async def forge_voltage_3v3_pkg_progressive_test(dut):
    test_level = os.getenv("TEST_LEVEL", "P1_BASIC")
    tests = ForgeVoltage3V3Tests(dut, test_level)
    await tests.run()
```

**Phase 4c: Update test_configs.py**

Add entries for the three new packages:

```python
"forge_voltage_3v3_pkg": {
    "wrapper": "forge_voltage_3v3_pkg_tb_wrapper",
    "test_module": "test_forge_voltage_3v3_pkg_progressive",
    "description": "0-3.3V voltage type package (TTL/digital domain)"
},
"forge_voltage_5v0_pkg": {
    "wrapper": "forge_voltage_5v0_pkg_tb_wrapper",
    "test_module": "test_forge_voltage_5v0_pkg_progressive",
    "description": "0-5.0V voltage type package (unipolar supply domain)"
},
"forge_voltage_5v_bipolar_pkg": {
    "wrapper": "forge_voltage_5v_bipolar_pkg_tb_wrapper",
    "test_module": "test_forge_voltage_5v_bipolar_pkg_progressive",
    "description": "±5.0V voltage type package (bipolar signal domain)"
},
```

**Phase 4d: Validation**

Run tests and verify P1 output <20 lines:

```bash
uv run python tests/run.py forge_voltage_3v3_pkg
uv run python tests/run.py forge_voltage_5v0_pkg
uv run python tests/run.py forge_voltage_5v_bipolar_pkg
```

**Phase 4e: Documentation Updates**

Update `CLAUDE.md` and `llms.txt` to reflect the new packages (replace volo_voltage_pkg references with the three new forge_voltage_*_pkg packages).

---

## Key Constraints

**CRITICAL CocoTB Interface Rules:**
- Test wrappers CANNOT have `real` or `boolean` types on entity ports
- Use only: `signed`, `unsigned`, `std_logic_vector`, `std_logic`
- Convert between digital and real internally within wrapper

**VHDL Coding Standards:**
- Follow forge-vhdl standards (see `docs/VHDL_CODING_STANDARDS.md`)
- Use std_logic_vector for FSM states (not enums)
- Port order: clk, rst_n, clk_en, enable, data, status
- Signal prefixes: ctrl_*, cfg_*, stat_*, dbg_*

**Progressive Testing Standard:**
- P1 tests MUST produce <20 lines of output
- Use small test values (3-4 tests for P1)
- Default filter level: AGGRESSIVE (98% noise reduction)
- Test structure: See `test_forge_util_clk_divider_progressive.py` as reference

---

## Files You Need To Reference

**Inside this submodule:**
- `CLAUDE.md` - Authoritative design guide (Section 4: CocoTB rules)
- `llms.txt` - Quick reference
- `.migration/VOLTAGE_TYPE_SYSTEM_DESIGN.md` - Complete design rationale
- `.migration/voltage_types_reference.py` - Python implementation reference
- `.migration/FORGE_VHDL_P4.md` - Detailed Phase 4 plan
- `vhdl/packages/volo_voltage_pkg.vhd` - Template to follow (legacy)
- `tests/test_volo_lut_pkg_progressive.py` - Test pattern example
- `tests/volo_lut_pkg_tb_wrapper.vhd` - Wrapper pattern example
- `tests/test_forge_util_clk_divider_progressive.py` - Test structure example

---

## Git Workflow

**You are already inside the submodule, so:**

```bash
# Check status
git status

# Make changes
# ... edit files ...

# Commit directly (no cd needed!)
git add vhdl/packages/forge_voltage_3v3_pkg.vhd
git add tests/test_forge_voltage_3v3_pkg_progressive.py
# ... etc ...

git commit -m "feat: Implement forge_voltage_3v3_pkg with CocoTB tests

Implements 0-3.3V unipolar voltage type package:
- Constants: V_MIN, V_MAX, SCALE_FACTOR
- Conversion functions: to_digital(), from_digital()
- Validation: is_valid(), clamp()
- Testbench helpers: is_voltage_equal()

Tests:
- P1: 4 basic tests (<20 line output)
- P2: 7 comprehensive tests

Related: .migration/FORGE_VHDL_P4.md
"

git push origin 20251104-vhdl-forge-dev
```

**When Phase 4 is complete**, the user will handle updating the parent monorepo reference.

---

## Success Criteria

Phase 4 is complete when:

- ✅ All 3 VHDL packages exist and compile
- ✅ All 3 test suites exist and pass
- ✅ P1 tests produce <20 lines output each
- ✅ test_configs.py updated
- ✅ CLAUDE.md updated to reference new packages
- ✅ llms.txt updated to reference new packages
- ✅ All changes committed in submodule

---

## Estimated Time

- VHDL packages: 2-3 hours (template-based, straightforward)
- CocoTB tests: 2-3 hours (follow established pattern)
- Documentation: 30 minutes
- **Total: 4-6 hours**

---

## Tips

1. **Copy-paste template approach**: Use volo_voltage_pkg.vhd as starting point, adjust constants
2. **Test incrementally**: Write one package → test it → move to next
3. **Validate early**: Run P1 tests immediately to ensure <20 line output
4. **Reference existing patterns**: test_volo_lut_pkg_progressive.py has the exact structure you need
5. **Don't overthink**: This is straightforward template instantiation, not novel design

---

## Getting Started Command

```bash
# Verify you're in the right place
pwd  # Should show: .../libs/forge-vhdl

# Read the design doc
cat .migration/VOLTAGE_TYPE_SYSTEM_DESIGN.md

# Check existing template
cat vhdl/packages/volo_voltage_pkg.vhd

# Create first package
# (copy volo_voltage_pkg.vhd → forge_voltage_3v3_pkg.vhd, adjust constants)

# Test immediately
uv run python tests/run.py forge_voltage_3v3_pkg
```

---

**Good luck! This is straightforward template work. You've got this! 🚀**
