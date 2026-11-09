# Nyr0 Pirate Coin Automation

A lightweight, automated loop utility for Fortnite matches. It automatically detects match completions, clicks **Play Again** (or **Play** from the lobby), performs anti-AFK actions, and tracks **Pirate Shop Access** drops in real-time.

## Features

- **Infinite Match Loop:** Automatically clicks "Play Again" upon elimination or "Play" if returned to the lobby.
- **Dedicated W + Space Thread:** Executes forward-jump movements every 3 seconds independently to avoid AFK kicks without slowing down screen scanning.
- **Pirate Shop Access Counter:** Detects and tracks on-screen "You Found Pirate Shop Access" notifications.
- **Fast Regional Scanning (ROI):** Scans only specific button areas to keep CPU usage low on laptops and lower-spec PCs.
- **Misclick Protection:** Avoids clicking "Report Player" buttons and automatically dismisses modal popups.
- **Custom Button Snip Tool:** Easily select and save custom "Play Again" buttons for different resolutions or UI scales.

## Quick Start

1. Install dependencies:
   ```cmd
   Install_Requirements.bat
   ```
2. Start the macro:
   ```cmd
   Start.bat
   ```
3. Join a match in Fortnite and press **F8** (or click **Start Automation** in the UI). Press **F8** again to stop.

## Note

Set Fortnite display mode to **Windowed Fullscreen** for the best detection accuracy.
