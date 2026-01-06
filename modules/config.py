import os
import json
from org.telegram.messenger import ApplicationLoader

class Config:
    def __init__(self):
        self.path = os.path.join(ApplicationLoader.applicationContext.getExternalFilesDir(None).getAbsolutePath(), "lyrics_pro_config.json")
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "text_size": 18,
            "wallpaper_url": "",
            "font_path": "",
            "text_color": "#FFFFFF"
        }

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.settings, f)
