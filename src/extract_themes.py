import sys
import json
import os
from pathlib import Path

# Add src to path to allow importing themes_manager
sys.path.append(str(Path(__file__).parent))

from themes_manager import ThemesManager

tm = ThemesManager()
themes_dir = Path(__file__).parent / 'themes'
themes_dir.mkdir(exist_ok=True)

for key, data in tm.available_themes.items():
    theme_file = themes_dir / f"{key}.json"
    with open(theme_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
print(f"Extracted {len(tm.available_themes)} themes to {themes_dir}")
