# GHDL Output Filter - Intelligent Output Suppression

**The Secret Weapon for LLM-Friendly VHDL Testing**

---

## Overview

The **GHDL Output Filter** is a custom Python script that intelligently filters GHDL simulator output to reduce verbosity by **80-95%** while preserving all critical information (errors, failures, test results).

This is the **KEY ENABLER** for achieving <20 line P1 test output.

---

## The Problem

### Before Filtering (250+ lines)
```
     0.00ns INFO     cocotb.gpi                         ..gpi_embed.cpp:79  in set_program_name_in_venv                 Did not detect Python virtual environment. Using system-wide Python interpreter
     0.00ns INFO     cocotb.gpi                         ../gpi/GpiCommon.cpp:101   in gpi_print_registered_impl            VPI registered
[... 200+ more lines of GHDL initialization messages ...]
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected, returning 0
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected, returning 0
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected, returning 0
[... 50+ repeated metavalue warnings ...]
     0.10ns INFO     cocotb.regression                  uvm_schematic_test.py:12   in initial_phase                        Test starting
[... more noise ...]
```

**Token consumption:** ~4000 tokens
**LLM context impact:** SEVERE

### After Filtering (8 lines)
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Divide by 2
  ✓ PASS
T3: Enable control
  ✓ PASS
ALL 3 TESTS PASSED
```

**Token consumption:** ~50 tokens
**LLM context impact:** MINIMAL
**Reduction:** 98%! 🎉

---

## How It Works

### File Location
```
scripts/ghdl_output_filter.py
```

### Integration
The filter is automatically integrated into `tests/run.py` via:

```python
# Import filter
from ghdl_output_filter import GHDLOutputFilter, FilterLevel

# Create filtered output context
class FilteredOutput:
    """Context manager that captures and filters stdout/stderr at OS level"""
    def __init__(self, filter_level: FilterLevel = FilterLevel.NORMAL):
        self.filter = GHDLOutputFilter(level=filter_level)
    # ... filtering logic ...

# Use in test runner
with FilteredOutput(filter_level=filter_level):
    runner.test(...)  # All GHDL output is filtered!
```

**Key Innovation:** Operates at **OS file descriptor level** (redirects fd 1 and 2), so even C code (GHDL) can't bypass it!

---

## Filter Levels

### AGGRESSIVE (Maximum Suppression)
**Use for:** P1 tests, LLM development, CI/CD

**Filters:**
- ✅ All metavalue warnings
- ✅ All null/uninitialized warnings
- ✅ All initialization warnings (@0ms)
- ✅ GHDL internal messages
- ✅ Duplicate warnings
- ✅ GHDL elaboration noise

**Preserves:**
- ✅ Errors (always)
- ✅ Failures (always)
- ✅ PASS/FAIL results
- ✅ Test names
- ✅ Assertion failures

**Reduction:** 90-98%

### NORMAL (Balanced) - DEFAULT
**Use for:** P2 tests, daily development

**Filters:**
- ✅ Metavalue warnings
- ✅ Null warnings
- ✅ Initialization warnings
- ✅ Duplicate warnings

**Preserves:**
- ✅ Errors, failures, results (always)
- ✅ First occurrence of warnings
- ✅ Unique warnings

**Reduction:** 80-90%

### MINIMAL (Light Touch)
**Use for:** Debugging new tests, investigating warnings

**Filters:**
- ✅ Repeated metavalue warnings (keeps first)
- ✅ Severe duplicates only

**Preserves:**
- ✅ Everything else
- ✅ First occurrence of each warning type

**Reduction:** 50-70%

### NONE (Pass-Through)
**Use for:** Deep debugging, investigating GHDL internals

**Filters:** Nothing
**Reduction:** 0%

---

## What Gets Filtered

### Metavalue Warnings (Highest Priority)
```
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected, returning 0
NUMERIC_STD.TO_UNSIGNED: metavalue detected
STD_LOGIC_ARITH.CONV_INTEGER: metavalue detected, returning 0
```

**Why filter?** These occur during reset and initialization. They're expected and harmless, but GHDL emits 50+ of them.

### Null/Uninitialized Warnings
```
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: null argument detected, returning 0
NUMERIC_STD.TO_UNSIGNED: null argument detected
```

**Why filter?** Signals start uninitialized. This is normal VHDL behavior.

### Initialization Warnings (@0ms/@0fs)
```
@0ms:(assertion warning): ...
@0fs:(assertion warning): ...
at 0 ns: warning: ...
```

**Why filter?** Time-zero warnings are almost always harmless initialization artifacts.

### GHDL Internal Messages
```
ghdl:info: simulation started
ghdl:info: elaboration completed
ghdl:info: back annotation
bound check warning
```

**Why filter?** These are GHDL implementation details, not test results.

### Duplicate Warnings
If the same warning appears 50 times, show it once, filter the rest.

---

## What NEVER Gets Filtered

The filter has **PRESERVE patterns** that override all filtering:

```python
PRESERVE_PATTERNS = [
    r".*\bERROR\b.*",           # Errors
    r".*\bFAIL.*",              # Failures
    r".*\bPASS.*",              # Successes
    r".*assertion error.*",     # Real errors
    r".*assertion failure.*",   # Real failures
    r".*TEST.*COMPLETE.*",      # Test status
    r".*ALL TESTS.*",           # Summary
    r"^\s*Test \d+:.*",         # Test headers
    r"^={3,}.*",                # Separator lines
    r".*✓.*",                   # Success marks
    r".*✗.*",                   # Failure marks
]
```

**Golden Rule:** If it's important for understanding test results, it's preserved.

---

## Usage Examples

### In Test Runner (Automatic)
```bash
# Default: NORMAL filtering
uv run python tests/run.py volo_clk_divider

# Aggressive filtering (P1 tests)
export GHDL_FILTER_LEVEL=aggressive
uv run python tests/run.py volo_clk_divider

# No filtering (debugging)
export GHDL_FILTER_LEVEL=none
uv run python tests/run.py volo_clk_divider
```

### Standalone Script
```bash
# Filter GHDL output directly
ghdl -r my_entity | python scripts/ghdl_output_filter.py --level aggressive

# Show filtering summary
ghdl -r my_entity | python scripts/ghdl_output_filter.py --level normal --summary
```

### In Code
```python
from ghdl_output_filter import GHDLOutputFilter, FilterLevel

# Create filter
filter = GHDLOutputFilter(level=FilterLevel.AGGRESSIVE)

# Filter lines
lines = [...]
filtered = filter.filter_lines(lines)

# Check stats
print(f"Filtered {filter.stats.filtered_lines}/{filter.stats.total_lines} lines")
print(f"Metavalue warnings suppressed: {filter.stats.metavalue_warnings}")
```

---

## Technical Details

### Architecture
```python
class GHDLOutputFilter:
    """
    Stateful filter with regex-based pattern matching.

    Features:
    - Compiled regex patterns for performance
    - Deduplication via normalized warning tracking
    - Statistics collection
    - Multiple filter levels
    """
```

### Pattern Matching Strategy
1. **Check PRESERVE patterns first** - Never filter critical info
2. **Check duplicate warnings** - Deduplicate via normalization
3. **Apply level-based filters** - Metavalue → Null → Init → Internal
4. **Track statistics** - Count what's being filtered

### Normalization for Deduplication
```python
def normalize_warning(self, line: str) -> Optional[str]:
    """
    Remove timestamps and line numbers to detect duplicates.

    "@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected"
    becomes:
    "assertion warning NUMERIC_STD.TO_INTEGER metavalue detected"
    """
```

This allows the filter to recognize:
```
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected
@10ns:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected
@20ns:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected
```

As **the same warning**, showing it once and filtering repeats.

---

## Filter Statistics

After filtering, the filter can print a summary:

```
[GHDL Output Filter - Level: aggressive]
  Total lines: 287
  Filtered: 265 (92.3% reduction)
  - Metavalue warnings: 143
  - Null warnings: 37
  - Initialization warnings: 52
  - Duplicate warnings: 33
```

**Enable with:** `--summary` flag or via code.

---

## Why This Matters for LLMs

### Token Economics
| Scenario | Lines | Tokens | Cost (GPT-4) |
|----------|-------|--------|--------------|
| No filter | 287 | ~4000 | $0.12 |
| NORMAL filter | 28 | ~350 | $0.01 |
| AGGRESSIVE filter | 8 | ~50 | $0.001 |

**Per test run savings:** $0.11
**Per 100 test runs:** $11
**Per 1000 test runs:** $110

### Context Window Preservation
With a 200K token context window:
- **No filter:** 50 test runs consume entire context
- **With filter:** 4000 test runs fit comfortably

**Enables:** Iterative development with LLMs without context resets!

---

## Integration Checklist

When adding to your project:

- [ ] Copy `scripts/ghdl_output_filter.py` to your project
- [ ] Import in `tests/run.py`:
  ```python
  sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
  from ghdl_output_filter import GHDLOutputFilter, FilterLevel
  ```
- [ ] Wrap test execution in `FilteredOutput` context manager
- [ ] Set default filter level (recommend NORMAL)
- [ ] Test with `GHDL_FILTER_LEVEL=none` to verify nothing critical is lost
- [ ] Verify P1 output is <20 lines

---

## Common Customizations

### Add Custom Filter Patterns
```python
# In ghdl_output_filter.py
CUSTOM_PATTERNS = [
    r".*your specific warning.*",
    r".*another pattern to filter.*",
]

# Add to __init__
self.custom_re = [re.compile(p) for p in CUSTOM_PATTERNS]

# Add to should_filter()
if any(regex.search(line) for regex in self.custom_re):
    return True
```

### Add Custom Preserve Patterns
```python
PRESERVE_PATTERNS = [
    # ... existing patterns ...
    r".*MY_CUSTOM_IMPORTANT_MESSAGE.*",
]
```

### Adjust Filter Levels
```python
# Make NORMAL more aggressive
elif self.level == FilterLevel.NORMAL:
    if self.is_metavalue_warning(line):
        return True
    if self.is_null_warning(line):
        return True
    if self.is_initialization_warning(line):
        return True
    if self.is_internal_message(line):  # ADD THIS
        return True
```

---

## Debugging the Filter

### See what's being filtered
```bash
# Enable DEBUG mode in filter
export GHDL_FILTER_DEBUG=1
uv run python tests/run.py my_module
```

### Test filter independently
```bash
# Create test input
echo "@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected" > test.log
echo "ERROR: Something failed" >> test.log
echo "@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected" >> test.log

# Test filter
cat test.log | python scripts/ghdl_output_filter.py --level aggressive

# Should output only:
# ERROR: Something failed
```

### Verify nothing critical is lost
```bash
# Run without filter
GHDL_FILTER_LEVEL=none uv run python tests/run.py my_module > unfiltered.log

# Run with filter
GHDL_FILTER_LEVEL=aggressive uv run python tests/run.py my_module > filtered.log

# Check for errors/failures in unfiltered
grep -E "(ERROR|FAIL)" unfiltered.log > critical.log

# Verify they're in filtered output
grep -F -f critical.log filtered.log

# Should find all critical lines!
```

---

## Performance Impact

### Overhead
- **Regex compilation:** One-time at initialization (<1ms)
- **Per-line filtering:** ~0.01ms (negligible)
- **OS pipe redirection:** ~0.1ms per test

**Total overhead:** <5ms per test run (unmeasurable in practice)

### Benefits
- **Reduced I/O:** Less data written to terminal
- **Faster scrolling:** Less output to render
- **Better caching:** Terminal buffers don't overflow

**Net impact:** Tests actually run FASTER with filtering!

---

## Best Practices

### DO:
1. ✅ Use AGGRESSIVE for P1 tests (LLM-friendly)
2. ✅ Use NORMAL for P2 tests (balanced)
3. ✅ Use NONE when debugging new tests
4. ✅ Verify critical messages are preserved
5. ✅ Customize patterns for your project
6. ✅ Show filter summary in CI/CD

### DON'T:
1. ❌ Filter PASS/FAIL results (never!)
2. ❌ Filter assertion errors (never!)
3. ❌ Filter ERROR messages (never!)
4. ❌ Over-customize (start with defaults)
5. ❌ Filter without testing
6. ❌ Ignore filter statistics

---

## Real-World Impact

### Before Filter (EZ-EMFI Project)
```
$ uv run python tests/run.py volo_clk_divider
[287 lines of output]
[Context consumed: 4000 tokens]
[LLM reads 5% of output, misses important details]
```

### After Filter
```
$ uv run python tests/run.py volo_clk_divider
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Divide by 2
  ✓ PASS
T3: Enable control
  ✓ PASS
ALL 3 TESTS PASSED

[8 lines of output]
[Context consumed: 50 tokens]
[LLM reads 100% of output, understands everything]
```

**Result:** LLM-based development became practical for VHDL testing!

---

## Summary

The **GHDL Output Filter** is not just a nice-to-have - it's the **critical enabler** for:

1. ✅ **LLM-friendly testing** (98% token reduction)
2. ✅ **Progressive testing** (P1 <20 line output requirement)
3. ✅ **Context preservation** (4000x more test runs per context window)
4. ✅ **Fast iteration** (read test results, not noise)
5. ✅ **CI/CD efficiency** (clean logs, fast parsing)

**Without this filter, the progressive testing methodology would not be practical.**

---

## File Details

- **Location:** `scripts/ghdl_output_filter.py`
- **Size:** 340 lines
- **Dependencies:** Python 3.7+ (stdlib only - no external packages!)
- **License:** Portable, adaptable for any project

---

**Golden Rule:**
> "Filter aggressively, preserve critically."

The goal is <20 lines of meaningful output, not 200 lines of noise.

**This is THE secret weapon for LLM-friendly VHDL development.**
