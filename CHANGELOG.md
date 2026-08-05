### What's New in v1.0.24

- **PowerShell Elevated Updater Engine**: Implemented elevated PowerShell update installer to guarantee file replacement in protected directories (`Program Files`) with automatic UAC fallback.
- **Eliminated Temp Directory Cleanup Warning**: Used `os._exit(0)` and cleared `_MEIPASS` environment variables on relaunch, completely suppressing PyInstaller's `Failed to remove temporary directory` popup dialog.
- **Clean Icon & Asset Relaunch**: Ensured environment variables and working directory are sanitized prior to restart so all logos and UI icons display immediately on update completion.
