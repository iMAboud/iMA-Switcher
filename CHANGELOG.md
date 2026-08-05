### What's New in v1.0.21

- **Deadlock-Free Update Engine**: Eliminated cross-thread module import locks that caused PyInstaller compiled executables to freeze on update checks.
- **SSL Fallback Handler**: Added automatic SSL verification fallback for Windows environments where PyInstaller bundle certificate paths fail.
- **Instant Status Response**: Guaranteed non-blocking background thread execution returning clean "Up to date" or update notifications within seconds.
