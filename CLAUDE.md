# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Run app: `python src/main.py`
- Build executable: `bash build.sh` or `pip install pyinstaller && pyinstaller --onefile --windowed main.py`
- Install build requirements (macOS): `bash build_requirements.sh`

## Code Style Guidelines
- **Formatting**: 4 spaces for indentation
- **Type hints**: Use for function parameters and return types (e.g., `dataset_name: str`, `-> List[Schema]`)
- **Documentation**: Use docstrings for functions (""" """)
- **Naming**:
  - Variables/functions: snake_case
  - Classes: PascalCase
  - Constants: UPPER_CASE
- **Error handling**: Use try/except with specific exception types
- **Imports**:
  - Order: standard lib, third-party, local modules
  - Group imports by type with a blank line between groups
- **UI component structure**: Define handler functions near their components
- **Logging**: Use the logging module for all message traces at appropriate levels
- **Threading**: Use ThreadPoolExecutor for parallel operations
- **Config management**: Use the existing load/save functions for configuration

## Project Structure
- `src/main.py`: Main application with Flet UI
- `src/dp_desktop/`: Core functionality modules
  - `download.py`: Functions for downloading datasets
  - `upload.py`: Functions for uploading files
  - `list_objects.py`: API functions for listing schemas and datasets
- `build.sh`: Script to build the desktop application 
- `build_requirements.sh`: Script to install build dependencies
- `assets/`: Directory for application assets