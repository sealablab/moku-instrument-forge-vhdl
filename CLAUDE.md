# forge-vhdl Design and Testing Guide

**Version:** 1.0
**Purpose:** VHDL utilities with token-efficient AI-assisted testing
**Audience:** Human developers and AI agents

---

## Project Overview

**forge-vhdl** provides reusable VHDL components for Moku custom instrument development,
with CocoTB progressive testing infrastructure optimized for LLM-friendly iteration.

**Key Innovation:** 98% test output reduction (287 lines → 8 lines) through GHDL
output filtering + progressive test levels (P1/P2/P3/P4).

---

## Architecture

### Three-Tier Documentation Pattern

**Tier 1: llms.txt** (~800 tokens)
- Quick component catalog
- Basic usage examples
- Pointers to Tier 2

**Tier 2: CLAUDE.md** (this file, ~3-5k tokens)
- Testing standards (AUTHORITATIVE)
- Design patterns
- Component integration

**Tier 3: Source Code** (load as needed, 5-10k tokens per component)
- VHDL implementations
- CocoTB tests
- Inline documentation

---

## CocoTB Progressive Testing Standard

### The Golden Rule

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

Default to silence. Escalate consciously. Preserve context religiously.

### Progressive Test Levels

**P1 - BASIC** (Default, LLM-optimized)
- 2-4 essential tests only
- Small test values (cycles=20)
- <20 line output, <100 tokens
- <5 second runtime
- **Environment:** `TEST_LEVEL=P1_BASIC` (default)

**P2 - INTERMEDIATE** (Standard validation)
- 5-10 tests with edge cases
- Realistic test values
- <50 line output
- <30 second runtime
- **Environment:** `TEST_LEVEL=P2_INTERMEDIATE`

**P3 - COMPREHENSIVE** (Full coverage)
- 15-25 tests with stress testing
- Boundary values, corner cases
- <100 line output
- <2 minute runtime
- **Environment:** `TEST_LEVEL=P3_COMPREHENSIVE`

**P4 - EXHAUSTIVE** (Debug mode)
- Unlimited tests, random testing
- Maximum verbosity
- **Environment:** `TEST_LEVEL=P4_EXHAUSTIVE`

### GHDL Output Filter Levels

**AGGRESSIVE** (Default for P1)
- 90-98% output reduction
- Filters: metavalue, null, init, internal, duplicates
- Preserves: errors, failures, PASS/FAIL, assertions

**NORMAL** (Balanced)
- 80-90% output reduction
- Filters: metavalue, null, init, duplicates
- Preserves: errors, failures, first warning occurrences

**MINIMAL** (Light touch)
- 50-70% output reduction
- Filters: duplicate metavalue warnings only

**NONE** (Pass-through)
- 0% filtering
- Use for debugging filter itself

**Environment:** `GHDL_FILTER_LEVEL=aggressive|normal|minimal|none`

---

## Component Naming Convention

### Pattern

- Entities: `forge_<category>_<function>`
- Packages: `forge_<domain>_pkg` or `volo_<domain>_pkg` (legacy)
- Test files: `test_<component>_progressive.py`

### Categories

- `forge_util_*` - Generic utilities (clk_divider, edge_detector, synchronizer)
- `forge_debug_*` - Debug infrastructure (fsm_observer, signal_tap)
- `forge_loader_*` - Memory initialization (bram_loader, config_loader)

### Examples

```
forge_util_clk_divider.vhd           # Programmable clock divider
forge_debug_fsm_observer.vhd         # FSM state observer (future)
forge_loader_bram.vhd                # BRAM initialization (future)
volo_lut_pkg.vhd                     # LUT package (legacy name kept)
volo_voltage_pkg.vhd                 # Voltage package (legacy name kept)
```

---

## Component Catalog

### Utilities (forge_util_*)

**forge_util_clk_divider**
- Function: Programmable clock divider
- Generics: MAX_DIV (bit width)
- Ports: clk_in, reset, enable, divisor, clk_out
- Tests: 3 P1, 4 P2
- Use case: Clock generation, FSM timing
- File: `vhdl/utilities/forge_util_clk_divider.vhd`

### Packages

**volo_lut_pkg**
- Function: Look-up table utilities
- Exports: Voltage/index conversion functions, LUT constants
- Tests: 4 P1, 4 P2, 1 P3
- Use case: Voltage discretization, LUT-based calculations
- Dependencies: volo_voltage_pkg
- File: `vhdl/packages/volo_lut_pkg.vhd`

**volo_voltage_pkg** (⚠️ Pending redesign)
- Function: Voltage conversion utilities
- Current: Hardcoded ±5V
- Planned: 3-range system (3.3V, 5V, ±5V)
- Tests: None yet
- File: `vhdl/packages/volo_voltage_pkg.vhd`

**volo_common_pkg**
- Function: Common constants and types
- Exports: VOLO_READY control scheme, BRAM loader protocol
- Tests: None yet
- File: `vhdl/packages/volo_common_pkg.vhd`

### Debugging (forge_debug_*)

**fsm_observer** (no tests yet)
- Function: Export FSM state to Moku registers for oscilloscope debugging
- Generics: NUM_STATES, V_MIN, V_MAX, FAULT_STATE_THRESHOLD
- Use case: Hardware FSM debugging without simulation
- File: `vhdl/debugging/fsm_observer.vhd`

### Loaders (forge_loader_*)

**volo_bram_loader** (no tests yet)
- Function: BRAM initialization from external sources
- Use case: LUT loading, configuration data
- File: `vhdl/loader/volo_bram_loader.vhd`

---

## Testing Workflow

### Running Tests

```bash
# Navigate to forge-vhdl
cd libs/forge-vhdl

# Run P1 tests (default, LLM-optimized)
uv run python tests/run.py forge_util_clk_divider

# Run P2 tests with more verbosity
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL \
  uv run python tests/run.py forge_util_clk_divider

# List all available tests
uv run python tests/run.py --list

# Run all tests
uv run python tests/run.py --all
```

### Adding Tests for New Components

See `docs/PROGRESSIVE_TESTING_GUIDE.md` for step-by-step instructions.

Quick summary:
1. Copy template from `test_forge_util_clk_divider_progressive.py`
2. Create `<component>_tests/` directory with constants + P1/P2 modules
3. Update `tests/test_configs.py` with component entry
4. Run tests, ensure <20 line P1 output

---

## Integration with forge/

### forge/ Code Generation
- Uses `basic-app-datatypes` for type system (12 voltage types)
- Generates VHDL shim + main template
- Auto-generates type packages (`basic_app_types_pkg.vhd`)

### forge-vhdl Utilities
- Provides practical utilities for manual VHDL in `*_main.vhd`
- Focus on 3 common voltage ranges (3.3V, 5V, ±5V)
- Standalone, works outside forge/ ecosystem

**Separation:**
- forge/ = Comprehensive, auto-generated, YAML-driven
- forge-vhdl = Pragmatic, hand-written, day-to-day

---

## Token Efficiency Metrics

### Before CocoTB + GHDL Filter

```
Test output: 287 lines
Token consumption: ~4000 tokens
LLM context impact: SEVERE
Cost per test: $0.12 (GPT-4)
```

### After CocoTB + GHDL Filter

```
Test output: 8 lines (P1), 20 lines (P2)
Token consumption: ~50 tokens (P1), ~150 tokens (P2)
LLM context impact: MINIMAL
Cost per test: $0.001 (GPT-4)
```

**Savings:** 98% reduction, 120x cost reduction

---

## Development Workflow

### Adding New Component

1. Write VHDL component in appropriate `vhdl/` subdirectory
2. Create CocoTB test using template
3. Run P1 tests, ensure <20 line output
4. Commit in submodule with descriptive message
5. Update `llms.txt` catalog
6. Add component section to this `CLAUDE.md`

### Modifying Existing Component

1. Make VHDL changes
2. Run existing tests (should still pass)
3. Add new tests if behavior changed
4. Commit in submodule

### Git Submodule Protocol

**CRITICAL:** All commits must be made inside `libs/forge-vhdl` submodule!

```bash
cd libs/forge-vhdl
git checkout 20251104-vhdl-forge-dev  # Ensure on feature branch
# make changes
git add .
git commit -m "descriptive message"
git push origin 20251104-vhdl-forge-dev
cd ../..
git add libs/forge-vhdl  # Update parent reference
git commit -m "chore: Update forge-vhdl submodule"
git push origin 20251104-vhdl-forge-dev
```

---

## Common Testing Patterns

### Pattern 1: Simple Entity Test

See `test_forge_util_clk_divider_progressive.py` for complete example.

```python
class ForgeUtilClkDividerTests(TestBase):
    async def run_p1_basic(self):
        await self.test("Reset", self.test_reset)
        await self.test("Divide by 2", self.test_divide_by_2)

    async def test_reset(self):
        await reset_active_low(self.dut)
        assert int(self.dut.clk_out.value) == 0
```

### Pattern 2: Package Test (Needs Wrapper)

See `test_volo_lut_pkg_progressive.py` + `volo_lut_pkg_tb_wrapper.vhd`.

```vhdl
-- Wrapper entity (packages can't be top-level)
entity volo_lut_pkg_tb_wrapper is
end entity;

architecture tb of volo_lut_pkg_tb_wrapper is
    -- Expose package functions/constants as signals
    signal test_constant : std_logic_vector(15 downto 0) := PACKAGE_CONSTANT;
end architecture;
```

---

## Related Documentation

### In forge-vhdl
- `docs/VOLO_COCOTB_TESTING_STANDARD.md` - Authoritative testing rules
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Step-by-step test creation
- `docs/GHDL_OUTPUT_FILTER.md` - How the filter works
- `docs/COCOTB_PATTERNS.md` - Quick reference patterns
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - Common pitfalls

### In Monorepo
- `docs/migration/FORGE_VHDL_PLAN.md` - Migration plan
- `.claude/shared/ARCHITECTURE_OVERVIEW.md` - Hierarchical architecture

---

**Last Updated:** 2025-11-04
**Maintainer:** Moku Instrument Forge Team
**Version:** 1.0.0
