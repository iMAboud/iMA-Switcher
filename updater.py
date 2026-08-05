import sys
import os
import subprocess
import threading
import logging
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

GITHUB_REPO = "iMAboud/iMA-Switcher"
COMMIT_URL = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
COMMIT_FALLBACK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/commits/master"
EXE_DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download/latest/iMA.Switcher.Installer.exe"

def get_current_commit():
    if getattr(sys, 'frozen', False):
        commit_file = Path(sys._MEIPASS) / "commit.txt"
        if commit_file.exists():
            return commit_file.read_text().strip()
        return "unknown_legacy_build"
    else:
        dev_commit_file = Path(__file__).parent / "commit.txt"
        if dev_commit_file.exists():
            return dev_commit_file.read_text().strip()
        return "dev_build"

def cleanup_old_exe():
    if getattr(sys, 'frozen', False):
        current_exe = Path(sys.executable)
        old_exe = current_exe.with_suffix(".old")
        tmp_exe = current_exe.with_suffix(".tmp")
        if old_exe.exists():
            try:
                old_exe.unlink()
            except Exception as error:
                logging.warning(f"Could not remove old executable: {error}")
        if tmp_exe.exists():
            try:
                tmp_exe.unlink()
            except Exception as error:
                logging.warning(f"Could not remove temporary executable: {error}")

RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def resolve_download_url():
    if requests is None:
        return EXE_DOWNLOAD_URL, 0
    try:
        headers = {"User-Agent": "iMA-Switcher-App"}
        res = requests.get(RELEASES_URL, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    return asset.get("browser_download_url"), asset.get("size", 0)
    except Exception:
        pass
    return EXE_DOWNLOAD_URL, 0

def check_for_commit_update():
    if requests is None:
        return False, get_current_commit(), "", EXE_DOWNLOAD_URL, "Requests library unavailable", 0

    current_sha = get_current_commit()
    headers = {"User-Agent": "iMA-Switcher-App", "Accept": "application/vnd.github.v3+json"}
    
    try:
        response = requests.get(COMMIT_URL, headers=headers, timeout=6)
        if response.status_code != 200:
            response = requests.get(COMMIT_FALLBACK_URL, headers=headers, timeout=6)
            
        if response.status_code != 200:
            return False, current_sha, "", EXE_DOWNLOAD_URL, f"GitHub API error {response.status_code}", 0

        commit_data = response.json()
        remote_sha = commit_data.get("sha", "").strip()
        commit_message = commit_data.get("commit", {}).get("message", "New commit published on GitHub.")

        has_update = bool(remote_sha and current_sha != "dev_build" and remote_sha[:7] != current_sha[:7])
        download_url, asset_size = resolve_download_url()

        return has_update, current_sha, remote_sha, download_url, commit_message, asset_size

    except Exception as error:
        logging.warning(f"Error checking commit update: {error}")
        return False, current_sha, "", EXE_DOWNLOAD_URL, str(error), 0

def download_and_apply_update(download_url=EXE_DOWNLOAD_URL, progress_callback=None):
    if requests is None:
        return False, "Requests library unavailable"

    current_exe = Path(sys.executable) if getattr(sys, 'frozen', False) else Path(__file__).parent / "iMA Switcher.exe"
    temp_exe = current_exe.with_suffix(".tmp")
    old_exe = current_exe.with_suffix(".old")

    try:
        if old_exe.exists():
            try:
                old_exe.unlink()
            except Exception:
                pass

        response = requests.get(download_url, stream=True, timeout=20)
        response.raise_for_status()
        total_bytes = int(response.headers.get('content-length', 0))
        downloaded_bytes = 0

        with open(temp_exe, "wb") as file_handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    file_handle.write(chunk)
                    downloaded_bytes += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded_bytes, total_bytes)

        if getattr(sys, 'frozen', False):
            current_exe.rename(old_exe)
            temp_exe.rename(current_exe)
            subprocess.Popen([str(current_exe)] + sys.argv[1:])
            from PyQt5.QtWidgets import QApplication
            app_instance = QApplication.instance()
            if app_instance:
                app_instance.quit()
            else:
                sys.exit(0)
            return True, "Update applied successfully"
        else:
            return True, "Downloaded update (Dev Mode)"

    except Exception as error:
        logging.error(f"Failed to apply commit update: {error}")
        if temp_exe.exists():
            try:
                temp_exe.unlink()
            except Exception:
                pass
        return False, str(error)

def start_background_auto_updater(on_update_found_callback=None):
    def _updater_worker():
        cleanup_old_exe()
        has_update, current_sha, remote_sha, download_url, commit_message, asset_size = check_for_commit_update()
        if has_update and on_update_found_callback:
            on_update_found_callback(current_sha, remote_sha, download_url, commit_message)

    threading.Thread(target=_updater_worker, daemon=True).start()
