# moku-instrument-forge-vhdl

Shared VHDL utilities for Moku custom instrument development using the forge framework.

## Overview

This library provides reusable VHDL components for building custom instruments on the Moku platform:

- **Packages** - Common data types, constants, and utilities
- **Debugging** - FSM observer for hardware debugging
- **Loader** - BRAM initialization utilities
- **Utilities** - Clock dividers, triggers, and other helpers

## Repository Structure

```
moku-instrument-forge-vhdl/
├── vhdl/
│   ├── packages/           # VHDL packages
│   │   ├── volo_common_pkg.vhd
│   │   ├── volo_lut_pkg.vhd
│   │   └── volo_voltage_pkg.vhd
│   ├── debugging/          # Debug utilities
│   │   └── fsm_observer.vhd
│   ├── loader/             # Data loading utilities
│   │   └── volo_bram_loader.vhd
│   └── utilities/          # Generic utilities
│       ├── volo_clk_divider.vhd
│       └── volo_voltage_threshold_trigger_core.vhd
├── tests/                  # CocotB tests for utilities
└── README.md
```

## Usage

This library is typically used as a git submodule in projects like `moku-instrument-forge-mono-repo`:

```bash
# Add as submodule
git submodule add https://github.com/sealablab/moku-instrument-forge-vhdl.git libs/forge-vhdl

# Initialize submodule
git submodule update --init --recursive
```

## Components

### Packages

**volo_common_pkg** - Common types and constants for Moku development
**volo_lut_pkg** - Look-up table utilities
**volo_voltage_pkg** - Voltage conversion and scaling utilities

### Debugging

**fsm_observer** - Real-time FSM state observation via output registers
- Exports FSM state to Moku registers for oscilloscope debugging
- Enables hardware validation without simulation
- See `.claude/commands/debug.md` for usage patterns

### Loader

**volo_bram_loader** - BRAM initialization from external sources

### Utilities

**volo_clk_divider** - Programmable clock divider
**volo_voltage_threshold_trigger_core** - Voltage threshold detection

## Development

### Requirements

- GHDL (VHDL compiler)
- CocotB (for testing)
- Python 3.10+ with uv

### Running Tests

```bash
# Install dependencies
uv sync

# Run all tests
pytest

# Run specific test
pytest tests/test_volo_voltage_pkg.py
```

## Integration with Forge

This library is designed to work alongside `moku-instrument-forge`:

- **forge** generates probe interface code (shim + main template)
- **forge-vhdl** provides reusable utilities for implementing custom logic
- Together they provide a complete development environment

## Version History

**v1.0.0** - Initial release
- Extracted from EZ-EMFI project
- Includes volo utilities and fsm_observer
- CocotB test infrastructure

## License

MIT License - See LICENSE file

## Contributing

This library is part of the Moku custom instrument ecosystem. When adding new utilities:

1. Add VHDL source to appropriate `vhdl/` subdirectory
2. Add CocotB tests to `tests/`
3. Update this README
4. Document usage patterns in `.claude/commands/`

## Related Projects

- [moku-instrument-forge](https://github.com/sealablab/moku-instrument-forge) - Code generation framework
- [moku-instrument-forge-mono-repo](https://github.com/sealablab/moku-instrument-forge-mono-repo) - Example monorepo structure
- [moku-models](https://github.com/sealablab/moku-models) - Platform data models
