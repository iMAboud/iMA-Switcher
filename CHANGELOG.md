### What's New in v1.0.22

- **Icon & Asset Retention Across Updates**: Configured detached process relaunch with explicit working directory (`cwd`), ensuring all logos, UI icons, and rank assets load instantly after auto-updating.
- **Clean Process Handshake**: Added `close_fds` and process tree detachment (`DETACHED_PROCESS`) to resolve PyInstaller temporary directory cleanup warnings on restart.
- **Deadlock-Free Update Engine**: Refactored update thread to guarantee non-blocking, sub-second update checks across all environments.
