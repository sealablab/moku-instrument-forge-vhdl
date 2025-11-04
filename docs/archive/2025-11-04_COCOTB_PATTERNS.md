# CocotB Testing Patterns Reference

**Quick reference for common CocotB patterns used in EZ-EMFI**

These patterns were developed/refined during Phase 2 progressive testing implementation.
Use this as a quick lookup when writing new tests.

---

## 0. CocoTB Interface Type Rules (CRITICAL) ⚠️

**READ THIS FIRST:** CocoTB has strict limitations on what VHDL types it can access through entity ports.

### Rule 1: Supported vs Unsupported Port Types

| Type | CocoTB Access | Use Case | Python Access Pattern |
|------|---------------|----------|----------------------|
| ✅ `std_logic` | **YES** | Single-bit signals | `int(dut.signal.value)` |
| ✅ `std_logic_vector` | **YES** | Unsigned multi-bit | `int(dut.signal.value)` |
| ✅ `unsigned` | **YES** | Unsigned integers | `int(dut.signal.value)` |
| ✅ `signed` | **YES** | Signed integers | `int(dut.signal.value.signed_integer)` |
| ❌ `real` | **NO** | Floating-point | ⛔ **ERROR: "contains no child object"** |
| ❌ `integer` | **PARTIAL** | Integer type | ⚠️ Use `signed` instead for reliability |
| ❌ `boolean` | **NO** | True/False | ⛔ **ERROR: "contains no child object"** |
| ❌ `time` | **NO** | Timing values | ⛔ Not accessible |
| ❌ `file` | **NO** | File handles | ⛔ Not accessible |
| ❌ Custom records | **NO** | Composite types | ⛔ Use separate signals |

### Rule 2: Signal Access Patterns

```python
# ✅ CORRECT: Accessing different types

# std_logic (single bit)
enable = int(dut.enable.value)  # Returns 0 or 1

# std_logic_vector / unsigned
data = int(dut.data.value)  # Returns unsigned integer

# signed (IMPORTANT: Use .signed_integer)
voltage = int(dut.voltage.value.signed_integer)  # Returns signed integer

# ❌ WRONG: Trying to access real or boolean
voltage = float(dut.voltage_real.value)  # ERROR: "contains no child object"
flag = bool(dut.is_valid.value)          # ERROR: "contains no child object"
```

### Rule 3: Test Wrapper Pattern for Packages

When testing packages that use `real` or `boolean` internally, you MUST use digital types at the entity boundary.

**❌ WRONG - CocoTB Cannot Access This:**

```vhdl
entity voltage_pkg_tb_wrapper is
    port (
        test_voltage : in real;              -- ❌ ERROR!
        test_digital : in signed(15 downto 0);

        digital_result : out signed(15 downto 0);
        voltage_result : out real;           -- ❌ ERROR!
        is_valid_result : out boolean;       -- ❌ ERROR!
        clamped_voltage : out real           -- ❌ ERROR!
    );
end entity;

architecture rtl of voltage_pkg_tb_wrapper is
begin
    -- This won't work with CocoTB!
    digital_result <= to_digital(test_voltage);
    voltage_result <= from_digital(test_digital);
    is_valid_result <= is_valid(test_voltage);
end architecture;
```

**✅ CORRECT - Use Digital Types with Registered Outputs:**

```vhdl
entity voltage_pkg_tb_wrapper is
    port (
        clk : in std_logic;
        reset : in std_logic;

        -- All inputs use digital types
        test_voltage_digital : in signed(15 downto 0);  -- ✅ Scaled voltage
        test_digital : in signed(15 downto 0);

        -- Function selects (one-hot)
        sel_to_digital : in std_logic;
        sel_from_digital : in std_logic;
        sel_is_valid : in std_logic;
        sel_clamp : in std_logic;

        -- All outputs use digital types (registered)
        digital_result : out signed(15 downto 0);       -- ✅ Works!
        voltage_result : out signed(15 downto 0);       -- ✅ Scaled voltage
        is_valid_result : out std_logic;                -- ✅ Boolean as std_logic
        clamped_result : out signed(15 downto 0)        -- ✅ Scaled voltage
    );
end entity;

architecture rtl of voltage_pkg_tb_wrapper is
    -- Internal real values for package functions
    signal voltage_real : real;
    signal voltage_out_real : real;
    signal clamped_real : real;
begin
    -- Convert digital input to real for package functions
    voltage_real <= from_digital(test_voltage_digital);

    -- Registered outputs prevent timing issues
    process(clk, reset)
    begin
        if reset = '1' then
            digital_result <= (others => '0');
            voltage_result <= (others => '0');
            is_valid_result <= '0';
            clamped_result <= (others => '0');

        elsif rising_edge(clk) then
            -- Test to_digital function
            if sel_to_digital = '1' then
                digital_result <= to_digital(voltage_real);
            end if;

            -- Test from_digital function (convert back to digital for output)
            if sel_from_digital = '1' then
                voltage_out_real <= from_digital(test_digital);
                voltage_result <= to_digital(voltage_out_real);
            end if;

            -- Test is_valid (convert boolean to std_logic)
            if sel_is_valid = '1' then
                if is_valid(voltage_real) then
                    is_valid_result <= '1';
                else
                    is_valid_result <= '0';
                end if;
            end if;

            -- Test clamp function
            if sel_clamp = '1' then
                clamped_real <= clamp(voltage_real);
                clamped_result <= to_digital(clamped_real);
            end if;
        end if;
    end process;
end architecture;
```

### Rule 4: Python Test Pattern

```python
import cocotb
from cocotb.triggers import RisingEdge
from conftest import setup_clock, reset_active_high

@cocotb.test()
async def test_voltage_package(dut):
    # Start clock
    await setup_clock(dut)
    await reset_active_high(dut)

    # Test to_digital: 2.5V in 0-5V range
    # Scale: 2.5V → (2.5/5.0) * 32767 = 16383
    dut.test_voltage_digital.value = 16383
    dut.sel_to_digital.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait for registration

    # ✅ CORRECT: Access signed output
    result = int(dut.digital_result.value.signed_integer)
    assert result == 16383, f"Expected 16383, got {result}"

    # Test is_valid: Check 3.3V (should be invalid for 0-5V range? Or valid?)
    # Depends on package implementation
    dut.test_voltage_digital.value = 21626  # 3.3V scaled
    dut.sel_to_digital.value = 0
    dut.sel_is_valid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # ✅ CORRECT: Access std_logic output (boolean → std_logic)
    is_valid = int(dut.is_valid_result.value)
    assert is_valid in [0, 1], f"Expected 0 or 1, got {is_valid}"
```

### Rule 5: Type Conversion Helpers

For packages that work with `real` types internally, add scaling helper functions:

```vhdl
-- In your package
package voltage_helpers_pkg is
    -- Convert digital (signed 16-bit) to voltage
    function digital_to_voltage(dig : signed) return real;

    -- Convert voltage to digital (signed 16-bit)
    function voltage_to_digital(volt : real) return signed;
end package;

package body voltage_helpers_pkg is
    function digital_to_voltage(dig : signed) return real is
        constant V_MIN : real := 0.0;
        constant V_MAX : real := 5.0;
    begin
        return V_MIN + (real(to_integer(dig)) / 32767.0) * (V_MAX - V_MIN);
    end function;

    function voltage_to_digital(volt : real) return signed is
        constant V_MIN : real := 0.0;
        constant V_MAX : real := 5.0;
        variable scaled : integer;
    begin
        scaled := integer((volt - V_MIN) / (V_MAX - V_MIN) * 32767.0);
        return to_signed(scaled, 16);
    end function;
end package body;
```

### Why These Rules Matter

1. **CocoTB uses VPI/VHPI** - These simulator interfaces have limited type support
2. **`real` and `boolean` are not synthesizable** - They're simulation-only types
3. **Hardware works with bits** - Digital types match actual hardware behavior
4. **Consistency** - Using digital types everywhere prevents interface mismatches

### Quick Checklist

Before creating a test wrapper:
- [ ] All entity ports use only: `std_logic`, `std_logic_vector`, `signed`, `unsigned`
- [ ] No `real`, `boolean`, `time`, `integer`, or custom record types in ports
- [ ] If package uses `real` internally, convert at wrapper boundary
- [ ] If package returns `boolean`, convert to `std_logic` (0/1) at wrapper boundary
- [ ] All outputs are registered (use `process(clk)` for timing stability)
- [ ] Python tests use correct access patterns (`.signed_integer` for signed types)

### See Also

- **Complete Example:** `tests/volo_lut_pkg_tb_wrapper.vhd` (correct pattern, no real types)
- **Section 5:** Signal persistence between tests
- **Section 9:** Test wrapper design patterns

---

## 1. Progressive Test Class Structure

**Pattern:** Inherit from TestBase and implement progressive run methods

```python
import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from <module>_tests.<module>_constants import *


class MyModuleTests(TestBase):
    """Progressive tests for my_module"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)  # MODULE_NAME from constants

    async def setup(self):
        """Common setup - runs before test phases"""
        await setup_clock(self.dut)
        # Module-specific initialization

    # P1 - Essential tests (2-4 tests, runs by default)
    async def run_p1_basic(self):
        await self.setup()
        await self.test("Test name", self.test_method)
        # Add 1-3 more essential tests

    # P2 - Comprehensive tests (runs when TEST_LEVEL=P2_INTERMEDIATE)
    async def run_p2_intermediate(self):
        await self.setup()
        await self.test("Edge case", self.test_edge_case)
        # Add more comprehensive tests

    async def test_method(self):
        """Individual test implementation"""
        # Test logic here
        assert condition, "Error message"
        self.log("Debug info", VerbosityLevel.VERBOSE)


@cocotb.test()
async def test_my_module(dut):
    """CocotB entry point"""
    tester = MyModuleTests(dut)
    await tester.run_all_tests()  # Automatically runs P1, then P2 if enabled
```

**Key Points:**
- `run_p1_basic()` is mandatory - runs by default
- `run_p2_intermediate()` runs when `TEST_LEVEL=P2_INTERMEDIATE`
- `self.test(name, func)` wraps tests with logging and error handling
- `self.log(msg, level)` for conditional logging

---

## 2. Constants File Organization

**Pattern:** Single source of truth for test parameters

```python
# tests/<module>_tests/<module>_constants.py
from pathlib import Path

MODULE_NAME = "my_module"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"

HDL_SOURCES = [
    VHDL_DIR / "my_module.vhd",
    # Add dependencies
]

HDL_TOPLEVEL = "my_module"  # Use lowercase (GHDL lowercases entity names)

# Test parameters - use small values for P1!
class TestValues:
    P1_TEST_CYCLES = 20       # Small = fast
    P1_DIV_VALUES = [2]

    P2_TEST_CYCLES = 100      # Realistic
    P2_DIV_VALUES = [1, 10, 255]

# Error messages with placeholders
class ErrorMessages:
    RESET_FAILED = "Reset check failed: expected {}, got {}"
    COUNT_MISMATCH = "Count mismatch: expected {}, got {} at cycle {}"
    TIMEOUT = "Operation timed out after {} cycles"

# Helper functions (if needed)
def calculate_expected_pulses(div_value: int, cycles: int) -> int:
    return cycles // div_value if div_value > 0 else cycles
```

**Key Points:**
- Keep P1 values SMALL for fast tests
- Use classes to organize related constants
- Format strings for clear error messages
- Include helper functions if useful

---

## 3. Common Test Utilities (from conftest.py)

**Pattern:** Use shared utilities to avoid duplication

### Clock and Reset

```python
from conftest import setup_clock, reset_active_low, reset_active_high

# Start clock (default 10ns period = 100MHz)
await setup_clock(dut)
await setup_clock(dut, period_ns=8)  # 125MHz
await setup_clock(dut, clk_signal="Clk")  # Non-default clock name

# Reset (active-low)
await reset_active_low(dut)
await reset_active_low(dut, rst_signal="rst_n")  # Non-default reset name

# Reset (active-high)
await reset_active_high(dut)
await reset_active_high(dut, rst_signal="Reset")
```

### Pulse Counting

```python
from conftest import count_pulses, assert_pulse_count

# Count pulses manually
pulse_count = await count_pulses(dut.clk_en, dut.clk, cycles=100)
assert pulse_count == expected, f"Expected {expected}, got {pulse_count}"

# Count + assert in one call
await assert_pulse_count(dut.clk_en, dut.clk, cycles=100, expected=10)
```

### MCC Utilities (for MCC-based modules)

```python
from conftest import init_mcc_inputs, mcc_set_regs, mcc_cr0

# Initialize MCC inputs to zero
await init_mcc_inputs(dut)

# Set control registers
await mcc_set_regs(dut, {
    0: mcc_cr0(),        # Enable with VOLO_READY bits
    20: 1,               # Armed
    21: 0,               # Force fire
    25: 10,              # Firing duration
})

# Create CR0 with VOLO_READY control
cr0_value = mcc_cr0()  # All control bits set (0xE0000000)
```

**Available utilities in conftest.py:**
- `setup_clock(dut, period_ns=10, clk_signal="clk")`
- `reset_active_low(dut, rst_signal="rst_n")`
- `reset_active_high(dut, rst_signal="reset")`
- `count_pulses(signal, clock, cycles)`
- `assert_pulse_count(signal, clock, cycles, expected)`
- `verify_division_ratio(signal, clock, div_value, cycles)`
- `init_mcc_inputs(dut)` - Initialize InputA/B/C to zero
- `mcc_set_regs(dut, regs_dict)` - Set control registers
- `mcc_cr0()` - Generate CR0 with VOLO_READY bits
- `run_with_timeout(coro, timeout_sec, test_name)` - Timeout wrapper

---

## 4. Conditional Logging

**Pattern:** Use verbosity levels to control output

```python
from test_base import VerbosityLevel

class MyTests(TestBase):
    async def test_something(self):
        # Only prints when COCOTB_VERBOSITY >= VERBOSE
        self.log(f"Debug: counter={count}", VerbosityLevel.VERBOSE)

        # Only prints when COCOTB_VERBOSITY >= NORMAL
        self.log("Starting test phase 2", VerbosityLevel.NORMAL)

        # Always prints (errors)
        if failed:
            self.log("Critical error!", VerbosityLevel.SILENT)
```

**Verbosity Levels:**
- `SILENT` (0) - Only failures (use for critical errors)
- `MINIMAL` (1) - Test names + PASS/FAIL (default)
- `NORMAL` (2) - Progress indicators
- `VERBOSE` (3) - Detailed logs
- `DEBUG` (4) - Everything

**Default is MINIMAL** - Test output is just:
```
T1: Test name
  ✓ PASS
```

---

## 5. Environment Variables

**Pattern:** Control test behavior via environment variables

### Test Levels

```bash
# Default: P1 only (fast, minimal output)
uv run python tests/run.py my_module

# P1 + P2 (comprehensive)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py my_module

# Future: P3 and P4
TEST_LEVEL=P3_COMPREHENSIVE uv run python tests/run.py my_module
TEST_LEVEL=P4_EXHAUSTIVE uv run python tests/run.py my_module
```

### Verbosity Control

```bash
# Minimal (default) - Just PASS/FAIL
uv run python tests/run.py my_module

# Normal - Add progress indicators
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py my_module

# Verbose - Detailed logs
COCOTB_VERBOSITY=VERBOSE uv run python tests/run.py my_module

# Debug - Everything
COCOTB_VERBOSITY=DEBUG uv run python tests/run.py my_module
```

### Combined

```bash
# Full tests with detailed output
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL uv run python tests/run.py my_module
```

---

## 6. Assertion Patterns

**Pattern:** Clear, informative assertions

### Basic Assertions

```python
# Bad - unclear
assert x == 0

# Good - clear error message
assert x == 0, f"Expected 0, got {x}"

# Better - use ErrorMessages from constants
assert x == 0, ErrorMessages.RESET_FAILED.format(0, x)
```

### Signal Assertions

```python
# Check signal value
output = int(dut.output.value)
assert output == expected, f"Output mismatch: expected {expected}, got {output}"

# Check signal exists
assert hasattr(dut, 'clk_en'), "Module should have clk_en signal"

# Check signed values
signed_val = int(dut.signed_signal.value.signed_integer)
assert signed_val == -100, f"Expected -100, got {signed_val}"
```

### State Assertions

```python
# FSM state checks
STATE_READY = 0b000
STATE_ARMED = 0b001

current_state = int(dut.state.value)
assert current_state == STATE_READY, f"Expected READY state, got {current_state:03b}"
```

---

## 7. Directory Structure Pattern

**Pattern:** Organized per-module test directories

```
tests/
├── <module>_tests/                  # Module-specific directory
│   ├── __init__.py                  # Package marker
│   ├── <module>_constants.py        # Shared constants
│   ├── P1_<module>_basic.py         # P1 tests (optional separate file)
│   └── P2_<module>_intermediate.py  # P2 tests (optional separate file)
└── test_<module>_progressive.py     # Main test file (required)
```

**Minimal structure** (constants + main test file):
```
tests/
├── <module>_tests/
│   ├── __init__.py
│   └── <module>_constants.py
└── test_<module>_progressive.py
```

**__init__.py content:**
```python
"""<Module> Progressive Test Suite"""
__all__ = ["<module>_constants"]
```

---

## 8. Test Execution Patterns

**Pattern:** How to run tests efficiently

### Single Module

```bash
# Quick P1 validation (default)
uv run python tests/run.py volo_clk_divider

# Full P2 validation
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider
```

### Multiple Modules

```bash
# Run all tests in a category
uv run python tests/run.py --category volo_modules

# Run all tests
uv run python tests/run.py --all
```

### With Options

```bash
# Disable waveforms (faster)
uv run python tests/run.py my_module --no-waves

# With verbose output
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py my_module
```

---

## 9. Common Gotchas

### Entity Name Casing

```python
# BAD - GHDL lowercases entity names
TESTS_CONFIG["my_module"] = TestConfig(
    toplevel="My_Module",  # Won't work!
)

# GOOD - Use lowercase
TESTS_CONFIG["my_module"] = TestConfig(
    toplevel="my_module",  # Works!
)
```

### Signal Access

```python
# Check if signal exists first
if hasattr(dut, 'enable'):
    dut.enable.value = 1

# Access nested signals
fsm_state = dut.U_FSM.current_state.value
```

### Imports

```python
# Always add parent directory to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Now you can import from tests/
from test_base import TestBase
from <module>_tests.<module>_constants import *
```

---

## 10. P1 Test Design Guidelines

**Pattern:** Keep P1 minimal and fast

### DO:
- ✅ Test 2-4 essential functions only
- ✅ Use small test values (cycles=20, not 10000)
- ✅ Verify reset behavior
- ✅ Test basic operation
- ✅ Test enable/disable control
- ✅ Keep output under 20 lines

### DON'T:
- ❌ Test every edge case (save for P2)
- ❌ Use large iteration counts
- ❌ Print debug info without verbosity control
- ❌ Test features already covered by dependencies

### Example P1 Split

**P1 (Essential - 3 tests):**
1. Reset behavior
2. Basic operation (divide by 2)
3. Enable control

**P2 (Comprehensive - 4 more tests):**
4. Bypass mode (divide by 1)
5. Typical operation (divide by 10)
6. Boundary condition (max division)
7. Status register visibility

---

## Quick Checklist for New Tests

When creating a new progressive test:

- [ ] Create `tests/<module>_tests/` directory
- [ ] Create `<module>_constants.py` with:
  - [ ] MODULE_NAME
  - [ ] HDL_SOURCES
  - [ ] HDL_TOPLEVEL (lowercase!)
  - [ ] TestValues class with P1/P2 values
  - [ ] ErrorMessages class
- [ ] Create `test_<module>_progressive.py` with:
  - [ ] Class inheriting from TestBase
  - [ ] `run_p1_basic()` method (2-4 tests)
  - [ ] `run_p2_intermediate()` method (optional)
  - [ ] `@cocotb.test()` entry point
- [ ] Update `test_configs.py`:
  - [ ] Add entry pointing to progressive test module
  - [ ] Use lowercase toplevel
- [ ] Test it:
  - [ ] P1 runs and produces <20 lines
  - [ ] P2 runs when TEST_LEVEL=P2_INTERMEDIATE
- [ ] Commit with descriptive message

---

## Example Test (Complete)

See working examples:
- **Simple:** `tests/volo_voltage_pkg_tests/` + `test_volo_voltage_pkg_progressive.py`
- **Complex:** `tests/volo_clk_divider_tests/` + `test_volo_clk_divider_progressive.py`

Both demonstrate the patterns above in real, working code.

---

**Last Updated:** 2025-01-27 (Phase 2)
**See Also:** `docs/PROGRESSIVE_TESTING_GUIDE.md` (comprehensive guide)
