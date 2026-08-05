### What's New in v1.0.23

- **Windows Batch Script Update Installer**: Solved `PermissionError: Access is Denied` by executing a 1-second delayed background script to replace the running executable after process exit.
- **Detailed Error Logging**: Enhanced update dialog and log output to display exact exception details if a download or update fails.
- **Release Tag Version Matching**: Fixed false-positive update flags by strictly matching release tags against `APP_VERSION`.
