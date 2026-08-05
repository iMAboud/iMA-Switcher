import sys
import os
import subprocess
import threading
import logging
from pathlib import Path

import re

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

def is_newer_version(remote_ver, local_ver):
    if not remote_ver or not local_ver:
        return False
    def parse(v):
        v = str(v).lstrip('vV').strip()
        parts = []
        for x in v.split('.'):
            try:
                num = re.sub(r'\D', '', x)
                parts.append(int(num) if num else 0)
            except Exception:
                parts.append(0)
        return parts
    return parse(remote_ver) > parse(local_ver)

def _safe_get(url, headers=None, timeout=6):
    if requests is None:
        return None
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code == 200:
            return res
    except Exception as error:
        logging.warning(f"Primary request failed for {url}: {error}")

    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        res = requests.get(url, headers=headers, timeout=timeout, verify=False)
        if res.status_code == 200:
            return res
    except Exception as error:
        logging.warning(f"Fallback SSL request failed for {url}: {error}")
    
    return None

def check_for_commit_update(local_version=None):
    if requests is None:
        return False, get_current_commit(), "", EXE_DOWNLOAD_URL, "Requests library unavailable", 0

    current_sha = get_current_commit()
    headers = {"User-Agent": "iMA-Switcher-App", "Accept": "application/vnd.github.v3+json"}
    
    commit_has_update = False
    remote_sha = ""
    commit_message = ""
    
    try:
        response = _safe_get(COMMIT_URL, headers=headers, timeout=6)
        if not response:
            response = _safe_get(COMMIT_FALLBACK_URL, headers=headers, timeout=6)
            
        if response and response.status_code == 200:
            commit_data = response.json()
            remote_sha = commit_data.get("sha", "").strip()
            commit_message = commit_data.get("commit", {}).get("message", "New commit published on GitHub.")
            if remote_sha and current_sha != "dev_build" and (current_sha == "unknown_legacy_build" or remote_sha[:7] != current_sha[:7]):
                commit_has_update = True
    except Exception as error:
        logging.warning(f"Error checking commit update: {error}")

    tag_has_update = False
    download_url, asset_size = EXE_DOWNLOAD_URL, 0
    tag_name = ""
    try:
        rel_res = _safe_get(RELEASES_URL, headers=headers, timeout=6)
        if rel_res and rel_res.status_code == 200:
            rel_data = rel_res.json()
            tag_name = rel_data.get("tag_name", "")
            rel_notes = rel_data.get("body", "")
            if rel_notes and not commit_message:
                commit_message = rel_notes
            for asset in rel_data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    asset_size = asset.get("size", 0)
                    break
            
            if tag_name and local_version and is_newer_version(tag_name, local_version):
                tag_has_update = True
    except Exception as error:
        logging.warning(f"Error checking release tag update: {error}")

    has_update = commit_has_update or tag_has_update
    if not commit_message:
        commit_message = f"New version {tag_name} available!" if tag_name else "New update published on GitHub."

    return has_update, current_sha, remote_sha or tag_name, download_url, commit_message, asset_size

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
