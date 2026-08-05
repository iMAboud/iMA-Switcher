import subprocess
import sys
import os
import shutil

# Get the directory of the build script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change the working directory to the script's directory
os.chdir(script_dir)

# Clean up previous build directories for a clean, optimized build
build_dir = os.path.join(script_dir, 'build')
dist_dir = os.path.join(script_dir, 'dist')

if os.path.exists(build_dir):
    print("Cleaning previous build folder...")
    try:
        shutil.rmtree(build_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning cleaning build dir: {e}")

try:
    # Run PyInstaller
    print("Starting optimized PyInstaller build...")
    subprocess.run(
        ['pyinstaller', '--noconfirm', 'InstallerTemp.spec'],
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
