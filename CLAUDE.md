# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development

```bash
# Install in editable mode
pip install -e .

# Run CLI
webpage-screenshot https://example.com -o output.png

# Docker
docker build -t webpage-screenshot .
docker run --rm -v $(pwd):/output webpage-screenshot https://example.com -o /output/example.png

# Docker for specific platforms
docker build -f Dockerfile.amd64 -t webpage-screenshot:amd64 .  # x86_64
docker build -f Dockerfile.arm64 -t webpage-screenshot:arm64 .  # ARM64
```

## Architecture

Single Python package (`webpage_screenshot/`) with three modules:

- `screenshot.py` - Core functionality: `take_screenshot()` function using Selenium CDP commands for full-page capture and smart resource loading detection
- `cli.py` - CLI argument parser with `--full-page`, `--wait`, `--auto-wait`, `--visible` flags
- `__init__.py` - Exports `take_screenshot`, `main`, and wait helper functions

**Dependencies**: Selenium 4.15+, Google Chrome browser (binary auto-detected from standard install paths)

**Key pattern**: `auto_wait` mode uses `wait_for_page_loaded()` to detect network idle (not just `document.readyState`), useful for SPAs.
