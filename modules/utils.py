import requests
import os
from java.io import File
from org.telegram.messenger import ApplicationLoader

def download_file(url, filename):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        cache_dir = ApplicationLoader.applicationContext.getExternalCacheDir()
        target_file = File(cache_dir, filename)
        with open(target_file.getAbsolutePath(), "wb") as f:
            f.write(response.content)
        return target_file.getAbsolutePath()
    except Exception as e:
        print(f"Download error: {e}")
        return None

def get_icon_id(name):
    from client_utils import get_last_fragment
    context = get_last_fragment().getContext()
    return context.getResources().getIdentifier(name, "drawable", context.getPackageName())
