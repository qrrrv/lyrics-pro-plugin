__id__ = "lyrics_pro"
__name__ = "Lyrics Pro"
__version__ = "2.2.0"
__author__ = "@PESSDES_Plugins"
__description__ = "Улучшенная версия Lyrics с кастомизацией обоев, шрифтов и размеров текста. (All-in-one version)"
__icon__ = "VoiceToText7/12"
__min_version__ = "11.12.1"

import os
import json
import requests
from base_plugin import BasePlugin, MethodHook
from client_utils import get_last_fragment, run_on_queue, get_media_controller
from dalvik.system import InMemoryDexClassLoader
from hook_utils import get_private_field, find_class
from java.io import File
from java.lang import Boolean, Integer
from java.nio import ByteBuffer
from org.telegram.messenger import ApplicationLoader, MessageObject
from org.telegram.ui.ActionBar import ActionBarMenuItem
from org.telegram.ui.Components import AudioPlayerAlert
from ui.bulletin import BulletinHelper
from ui.settings import Header, Text, Divider, Input
from android.graphics import Typeface, Color

# ======================================================
# КОНСТАНТЫ
# ======================================================
DEX_URL = "https://github.com/Hazzz895/ExteraPluginsAssets/raw/refs/heads/main/lyrics/dex/classes.dex"
CONTROLLER_CLASS_NAME = "com.pessdes.lyrics.components.lrclib.LyricsController"
SHOW_LYRICS_ITEM_ID = 6767

# ======================================================
# УПРАВЛЕНИЕ НАСТРОЙКАМИ
# ======================================================
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

# ======================================================
# ЛОГИКА КОНТРОЛЛЕРА
# ======================================================
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
                app_class_loader = ApplicationLoader.applicationContext.getClassLoader()
                dex_loader = InMemoryDexClassLoader(ByteBuffer.wrap(dex_bytes), app_class_loader)
                lyrics_controller_class = dex_loader.loadClass(CONTROLLER_CLASS_NAME)

            self.controller = lyrics_controller_class.getDeclaredMethod("getInstance").invoke(None)
            self.controller.initPluginController(plugin_name)
            return True
        except Exception as e:
            print(f"DEX Load Error: {e}")
            return False

# ======================================================
# ОСНОВНОЙ КЛАСС ПЛАГИНА
# ======================================================
class Plugin(BasePlugin):
    def __init__(self):
        self.config = Config()
        self.lyrics_manager = LyricsManager.get_instance()
        self.typeface = None

    def on_plugin_load(self):
        self.hook_method(AudioPlayerAlert.getClass().getDeclaredConstructors()[0], AudioPlayerAlertHook())
        self.hook_method(AudioPlayerAlert.getClass().getDeclaredMethod("updateTitle", Boolean.TYPE), UpdateHook())
        self.hook_method(AudioPlayerAlert.getClass().getDeclaredMethod("onSubItemClick", Integer.TYPE), SubItemClickHook())

        run_on_queue(lambda: self.lyrics_manager.load_dex(__name__))
        self.apply_custom_font()

    def apply_custom_font(self):
        font_path = self.config.settings.get("font_path")
        if font_path and os.path.exists(font_path):
            try:
                self.typeface = Typeface.createFromFile(font_path)
                if self.lyrics_manager.controller:
                    self.lyrics_manager.controller.setTypeface(self.typeface)
            except:
                pass

    def on_plugin_settings(self):
        return [
            Header("Настройки текста"),
            Input("Размер текста", value=str(self.config.settings["text_size"]), 
                  on_change=lambda v: self.update_setting("text_size", int(v) if v.isdigit() else 18)),
            Input("Цвет текста (HEX)", value=self.config.settings["text_color"], 
                  on_change=lambda v: self.update_setting("text_color", v)),
            Divider(),
            Header("Внешний вид"),
            Input("URL Обоев", value=self.config.settings["wallpaper_url"], 
                  on_change=lambda v: self.update_setting("wallpaper_url", v)),
            Input("Путь к шрифту (.ttf)", value=self.config.settings["font_path"], 
                  on_change=lambda v: self.update_setting("font_path", v)),
            Text("Для применения шрифта может потребоваться перезапуск")
        ]

    def update_setting(self, key, value):
        self.config.settings[key] = value
        self.config.save()
        
        if key == "text_size" and self.lyrics_manager.controller:
            try:
                self.lyrics_manager.controller.setTextSize(float(value))
            except:
                pass
        elif key == "text_color" and self.lyrics_manager.controller:
            try:
                color = Color.parseColor(value)
                self.lyrics_manager.controller.setTextColor(color)
            except:
                pass
        elif key == "wallpaper_url" and value:
            run_on_queue(lambda: self.download_wallpaper(value))

    def download_wallpaper(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            cache_dir = ApplicationLoader.applicationContext.getExternalCacheDir()
            wallpaper_file = File(cache_dir, "lyrics_wallpaper.jpg")
            with open(wallpaper_file.getAbsolutePath(), "wb") as f:
                f.write(response.content)
            
            if self.lyrics_manager.controller:
                try:
                    self.lyrics_manager.controller.setBackgroundPath(wallpaper_file.getAbsolutePath())
                except:
                    pass
        except:
            pass

# ======================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ХУКИ
# ======================================================
def is_music():
    playing = get_media_controller().getInstance().getPlayingMessageObject()
    return playing and playing.isMusic()

def get_icon_id(name):
    context = get_last_fragment().getContext()
    return context.getResources().getIdentifier(name, "drawable", context.getPackageName())

class AudioPlayerAlertHook(MethodHook):
    def after_hooked_method(self, param):
        optionsButton = get_private_field(param.thisObject, "optionsButton")
        icon_id = get_icon_id("msg_photo_text2")
        optionsButton.addSubItem(SHOW_LYRICS_ITEM_ID, icon_id, "Показать текст")
        optionsButton.setSubItemShown(SHOW_LYRICS_ITEM_ID, is_music())

class UpdateHook(MethodHook):
    def after_hooked_method(self, param):
        optionsButton = get_private_field(param.thisObject, "optionsButton")
        optionsButton.setSubItemShown(SHOW_LYRICS_ITEM_ID, is_music())

class SubItemClickHook(MethodHook):
    def before_hooked_method(self, param):
        if param.args[0] == SHOW_LYRICS_ITEM_ID:
            manager = LyricsManager.get_instance()
            if manager.controller:
                param.setResult(None)
                manager.controller.presentLyricsActivity(get_last_fragment())
            else:
                BulletinHelper.show_error("Контроллер не загружен!")
