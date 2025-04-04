# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Run app: `python main.py`
- Build executable: `bash build.sh` or `pip install pyinstaller && pyinstaller --onefile --windowed main.py`

## Code Style Guidelines
- Use docstrings for functions (""" """)
- Variable naming: snake_case
- Function naming: snake_case
- Error handling: Use try/except with specific exception types
- Indentation: 4 spaces
- Import order: standard library, third-party, local modules
- Type hints: Use for function parameters (e.g., `page: ft.Page`)
- UI component structure: Follow the existing pattern of defining handlers near their components
- Config management: Use the existing load/save functions for configuration

## Project Structure
- `main.py`: Main application code with Flet UI
- `config.json`: Stores the API key
- `build.sh`: Script to build the desktop application
- `requirements.txt`: Project dependencies
- `assets/`: Directory for application assets
  - `logo.png`: Application logo