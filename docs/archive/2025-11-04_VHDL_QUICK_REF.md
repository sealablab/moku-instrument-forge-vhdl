# VHDL Quick Reference Card

**For forge-vhdl development**
**Quick lookup for mandatory patterns**

---

## Port Order Template

```vhdl
entity forge_module_example is
    generic (
        PARAM : natural := 16  -- Generics first
    );
    port (
        -- 1. Clock & Reset
        clk    : in std_logic;
        rst_n  : in std_logic;  -- Active-low

        -- 2. Control
        clk_en : in std_logic;
        enable : in std_logic;

        -- 3. Data inputs
        data_in : in std_logic_vector(15 downto 0);

        -- 4. Data outputs
        data_out : out std_logic_vector(15 downto 0);

        -- 5. Status
        busy  : out std_logic;
        fault : out std_logic
    );
end entity;
```

**Mandatory order:** clk, rst_n, clk_en, enable, data, status

---

## FSM State Declaration Template

```vhdl
-- ✅ ALWAYS use std_logic_vector (NOT enums!)
constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
constant STATE_ARMED  : std_logic_vector(1 downto 0) := "01";
constant STATE_FIRING : std_logic_vector(1 downto 0) := "10";
constant STATE_DONE   : std_logic_vector(1 downto 0) := "11";

signal state, next_state : std_logic_vector(1 downto 0);
```

**Why:** Verilog compatibility + synthesis predictability

❌ **NEVER use enums** for FSM states!

---

## Signal Naming Prefixes

| Prefix | Purpose | Example |
|--------|---------|---------|
| `ctrl_` | Control signals | `ctrl_enable`, `ctrl_arm` |
| `cfg_` | Configuration | `cfg_threshold`, `cfg_mode` |
| `stat_` | Status outputs | `stat_busy`, `stat_fault` |
| `dbg_` | Debug outputs | `dbg_state_voltage` |
| `_n` | Active-low | `rst_n`, `enable_n` |
| `_next` | Next-state | `state_next` |
| `_r` | Registered | `data_r` |

**Apply universally** to ALL modules for consistency.

---

## Clocked Process Template

```vhdl
process(clk, rst_n)
begin
    if rst_n = '0' then
        -- 1. RESET (highest priority)
        output <= (others => '0');
        state  <= STATE_IDLE;

    elsif rising_edge(clk) then
        if clk_en = '1' then
            -- 2. CLK_EN (clock gating)

            if enable = '1' then
                -- 3. ENABLE (functional logic)
                output <= input;
                state  <= next_state;
            end if;
        end if;
    end if;
end process;
```

**Hierarchy:** rst_n > clk_en > enable

---

## FSM Process Template

```vhdl
-- State register (sequential)
FSM_REG: process(clk, rst_n)
begin
    if rst_n = '0' then
        state <= STATE_IDLE;
    elsif rising_edge(clk) then
        if clk_en = '1' then
            state <= next_state;
        end if;
    end if;
end process;

-- Next-state logic (combinational)
FSM_LOGIC: process(state, inputs)
begin
    next_state <= state;  -- Default: hold state

    case state is
        when STATE_IDLE =>
            if trigger = '1' then
                next_state <= STATE_ARMED;
            end if;

        when STATE_ARMED =>
            if fire_condition then
                next_state <= STATE_FIRING;
            end if;

        when STATE_FIRING =>
            if done then
                next_state <= STATE_DONE;
            end if;

        when others =>
            next_state <= STATE_IDLE;  -- Safe default
    end case;
end process;
```

**Always include:** `when others` clause

---

## Package Structure Template

```vhdl
package forge_module_pkg is

    ----------------------------------------------------------------------------
    -- Constants
    ----------------------------------------------------------------------------
    constant DATA_WIDTH : natural := 16;

    ----------------------------------------------------------------------------
    -- FSM States (std_logic_vector, not enum!)
    ----------------------------------------------------------------------------
    constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
    constant STATE_ACTIVE : std_logic_vector(1 downto 0) := "01";

    ----------------------------------------------------------------------------
    -- Status Register Bits
    ----------------------------------------------------------------------------
    constant STATUS_READY_BIT : natural := 0;
    constant STATUS_FAULT_BIT : natural := 7;  -- ALWAYS bit 7 for faults

    ----------------------------------------------------------------------------
    -- Helper Functions
    ----------------------------------------------------------------------------
    function clamp(value : signed; max_val : signed) return signed;

end package;
```

---

## Synthesis Safety Checklist

Before committing:

- [ ] FSM states use `std_logic_vector` (not enums)
- [ ] All case statements have `when others`
- [ ] All signals have default/reset values
- [ ] Port order: clk, rst_n, clk_en, enable, data, status
- [ ] Active-low reset (`rst_n`)
- [ ] No latches inferred (complete sensitivity/case coverage)
- [ ] Signal names follow prefix conventions
- [ ] Code synthesizes without warnings

---

## Common Anti-Patterns to Avoid

❌ **Enums for FSM states** → Use `std_logic_vector`
❌ **Incomplete case coverage** → Add `when others`
❌ **Multiple drivers** → One process per signal
❌ **Incomplete sensitivity** → List all inputs or use clocked
❌ **Latches** → Provide default assignments

---

**See full guide:** `docs/VHDL_CODING_STANDARDS.md`
**Last Updated:** 2025-11-04
