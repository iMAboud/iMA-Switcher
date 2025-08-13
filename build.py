import subprocess
import sys
import os

# Get the directory of the build script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change the working directory to the script's directory
os.chdir(script_dir)

try:
    # Run PyInstaller
    print("Starting PyInstaller build...")
    subprocess.run(
        ['pyinstaller', 'InstallerTemp.spec'],
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    print("\nBuild successful!")
    print(f"The executable can be found in the '{os.path.join(script_dir, 'dist')}' directory.")

except FileNotFoundError:
    print("\nError: 'pyinstaller' command not found.")
    print("Please ensure PyInstaller is installed and in your system's PATH.")
    print("You can install it by running: pip install pyinstaller")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"\nAn error occurred during the build process: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    sys.exit(1)
