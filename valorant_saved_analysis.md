# VALORANT `Saved` Folder Analysis & iMA Switcher Improvements

Based on the analysis of the `VALORANT/Saved` directory and the current `iMA Switcher` codebase, here are the findings and suggestions.

## 1. Contents of the `Saved` Folder
The `Saved` folder (`%LOCALAPPDATA%\VALORANT\Saved` or in your project) is strictly used for storing local client configurations, cache, and logs.

### What it DOES contain:
Inside `Saved\Config\<Account-GUID>-<Region>\`:
- **`RiotUserSettings.ini`**: Contains highly detailed settings such as:
  - **Crosshair Profiles**: Stored as a large JSON payload under `EAresStringSettingName::SavedCrosshairProfileData`. It includes colors, thicknesses, dot sizes, and multiple profiles per account.
  - **Audio Settings**: Volumes for Voice, Music, SFX, etc.
  - **Mouse Sensitivity**: Including ADS and Zoomed multipliers.
  - **Minimap settings**: Sizes and rotation preferences.
- **`GameUserSettings.ini`**: Contains system and graphical settings like:
  - Resolution, Window Mode (Fullscreen/Windowed).
  - Scalability groups (e.g., `sg.TextureQuality`, `sg.ShadowQuality`).
  - Frame rate limits.
- **`BackupKeybinds.json`**: Contains all the custom keybindings mapped to actions (e.g., ability bindings, movement, comms wheel).

### What it DOES NOT contain:
- **No Last Match Info:** You will not find KDA, maps played, or agents selected.
- **Why?** Riot Games enforces a strictly server-authoritative architecture. Match history, MMR, and inventory are never cached in plaintext locally to prevent tampering and stat manipulation. 

**Suggestion for fetching match data:** To get match info, KDA, or agents, you must use the unofficial Riot Client local API. You need to fetch the local lockfile at `%LOCALAPPDATA%\Riot Games\Riot Client\Config\lockfile`, read the auth token, and then query the local endpoints (or remote endpoints `pd.<region>.a.pvp.net`) directly for match history.

---

## 2. Issues & Improvements in iMA Switcher

### Current State
Currently, `iMA Switcher` handles account switching by swapping out the `Riot Client\Data` directory (which holds the login session tokens). It also seems to have a function `update_all_game_user_settings(graphics_settings)` to force some global graphics settings across all accounts.

However, Valorant natively handles per-account crosshairs and keybinds by creating a unique `<GUID>` folder in `Saved\Config\` for every account you log into.

### What is Missing / Done Wrong?
1. **Isolated vs Global Syncing**: Because Valorant uses unique GUID folders, if a user changes their crosshair or keybind on Account A, it will *not* reflect on Account B. iMA Switcher currently doesn't manage these GUID folders, so users have to manually redo settings for every smurf account.
2. **Identifying GUIDs**: iMA Switcher doesn't currently map a saved account name (e.g., "Main Account") to its Riot GUID. Without this mapping, you can't edit settings for a specific offline account.

### How to Improve Settings & Crosshairs
To add features for editing crosshairs per-account and globally, you should implement the following structure:

#### A. Map Accounts to PUUIDs (GUIDs)
You need to extract the player's PUUID (which is the GUID used in the folder name).
- When a user logs in via iMA Switcher, read the Riot Client's `lockfile` or logs to extract the PUUID.
- Save this PUUID in your `game.json` for that account profile (it seems you have a PUUID field but you must ensure it matches the folder name exactly).

#### B. Global Settings Sync Feature
Add a feature in iMA Switcher: "Sync Settings Across All Accounts".
1. The user selects a "Master Account" in iMA Switcher.
2. The app finds the PUUID for this master account, and reads the `RiotUserSettings.ini`, `GameUserSettings.ini`, and `BackupKeybinds.json` from its GUID folder inside `Saved\Config\`.
3. The app iterates through all other known PUUID folders in `VALORANT\Saved\Config\` and copies the Master's files to them.
4. *Result*: Perfect 1:1 crosshairs, sensitivities, and keybinds across all smurfs.

#### C. Crosshair Editor UI
Since `RiotUserSettings.ini` stores crosshairs as a standard JSON string:
1. Parse the JSON from `EAresStringSettingName::SavedCrosshairProfileData` for the active account's PUUID folder.
2. Build a UI in PyQt5 that decodes the JSON values (Inner lines, Outer lines, Colors).
3. Allow the user to inject a downloaded Crosshair Profile code directly into the JSON and save the `.ini`, preventing the user from needing to open the game to edit crosshairs.

#### D. Clean up Leftover Data
Over time, the `webcache` and `Logs` folders inside `Saved` bloat to several gigabytes. iMA Switcher already cleans some temp files (`_cleanup_valorant_temp_files`), but adding an explicit "Deep Clean Valorant Cache" button that wipes `Saved\webcache` and `Saved\Crashes` would be a great quality-of-life feature.
