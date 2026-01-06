import requests
from dalvik.system import InMemoryDexClassLoader
from java.nio import ByteBuffer
from hook_utils import find_class

DEX_URL = "https://github.com/Hazzz895/ExteraPluginsAssets/raw/refs/heads/main/lyrics/dex/classes.dex"
CONTROLLER_CLASS_NAME = "com.pessdes.lyrics.components.lrclib.LyricsController"

class LyricsManager:
    _instance = None
    controller = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_dex(self, plugin_name):
        try:
            lyrics_controller_class = None
            try:
                lyrics_controller_class = find_class(CONTROLLER_CLASS_NAME).getClass()
            except:
                pass

            if not lyrics_controller_class:
                response = requests.get(DEX_URL)
                response.raise_for_status()
                dex_bytes = response.content
                from org.telegram.messenger import ApplicationLoader
                app_class_loader = ApplicationLoader.applicationContext.getClassLoader()
                dex_loader = InMemoryDexClassLoader(ByteBuffer.wrap(dex_bytes), app_class_loader)
                lyrics_controller_class = dex_loader.loadClass(CONTROLLER_CLASS_NAME)

            self.controller = lyrics_controller_class.getDeclaredMethod("getInstance").invoke(None)
            self.controller.initPluginController(plugin_name)
            return True
        except Exception as e:
            print(f"DEX Load Error: {e}")
            return False
