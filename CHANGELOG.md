### What's New in v1.0.25

- **Native Update Installer Subprocess**: Redesigned auto-updater to use a clean subprocess handshake (`--update --pid <PID>`). Eliminated all script files (`.ps1`, `.bat`), terminal windows, and OS-level execution policy errors.
- **Graceful Application Teardown**: Updated app to exit using standard Qt event loop methods (`QApplication.quit()`), allowing PyInstaller to cleanly unload DLLs and remove temporary directories without errors.
- **Native Process Wait**: Added Win32 process wait logic to ensure file replacement occurs cleanly after parent process shutdown, preventing file lock conflicts.
