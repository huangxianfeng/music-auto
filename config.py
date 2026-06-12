import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    "target_url": "https://music.douyin.com/console",
    "headless": False,
    "window_size": (1440, 900),
    "download_dir": os.path.join(BASE_DIR, "downloads"),
    "uploads_dir": os.path.join(BASE_DIR, "uploads"),
    "outputs_dir": os.path.join(BASE_DIR, "outputs"),
    "user_data_dir": os.path.join(BASE_DIR, "chrome_profile"),
    "page_load_timeout": 60,
    "implicit_wait": 10,
    "default_lang": "zh-CN",
}

for key in ("download_dir", "uploads_dir", "outputs_dir", "user_data_dir"):
    os.makedirs(CONFIG[key], exist_ok=True)
