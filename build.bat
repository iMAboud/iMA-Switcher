@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building the application...
pyinstaller InstallerTemp.spec

echo Build complete. The installer is in the 'dist' directory.
pause
