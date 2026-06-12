import os
import random
import logging
import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)


# 简易主题词库，用于示例生成
THEMES = {
    "抒情": ["月光", "回忆", "远方", "时光", "思念", "晚风"],
    "励志": ["向前", "梦想", "远方", "星辰", "奔跑", "自由"],
    "爱情": ["心动", "温柔", "相遇", "牵手", "约定", "永恒"],
    "古风": ["明月", "山河", "故人", "青衫", "烟雨", "长亭"],
}

DEFAULT_LINES = [
    "在城市的尽头，我听见风的声音",
    "它轻轻地说，不要放弃前行",
    "每一颗星星，都藏着一个秘密",
    "愿你眼里有光，愿你心里有梦",
]


def generate_lyrics(theme: str = "励志", lines: int = 8) -> str:
    """基于主题词生成简单歌词文本。可替换为接入大模型 API。"""
    theme_words = THEMES.get(theme, THEMES["励志"])
    templates = [
        "我看见{w1}在{w2}中闪耀",
        "{w1}啊{w1}，带我去{w2}",
        "当{w1}落下，{w2}升起",
        "{w1}是我心里不灭的{w2}",
        "向着{w1}，追着{w2}",
        "{w1}与{w2}，从未离开",
    ]
    out: List[str] = []
    for i in range(lines):
        tpl = templates[i % len(templates)]
        w1, w2 = random.sample(theme_words, 2)
        out.append(tpl.format(w1=w1, w2=w2))
    lyrics = "\n".join(out)
    logger.info("已生成歌词（主题=%s，共 %d 行）", theme, lines)
    return lyrics


def save_lyrics(lyrics: str, filename: Optional[str] = None, out_dir: str = None) -> str:
    from config import CONFIG

    out_dir = out_dir or CONFIG["outputs_dir"]
    if not filename:
        filename = f"lyrics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(lyrics)
    logger.info("歌词已保存: %s", path)
    return path


def generate_music_placeholder(
    title: str = "auto_song", out_dir: Optional[str] = None
) -> str:
    """
    音乐生成占位方法：
    - 实际使用时可替换为调用 Suno / MusicGen / 抖音自带 AI 音乐等接口。
    - 这里仅在本地 outputs 下生成一个空占位文件，方便后续上传流程联调。
    """
    from config import CONFIG

    out_dir = out_dir or CONFIG["outputs_dir"]
    path = os.path.join(out_dir, f"{title}.mp3")
    with open(path, "wb") as f:
        f.write(b"")
    logger.info("音乐占位文件已生成: %s", path)
    return path


def build_prompt(theme: str, mood: str = "轻快") -> str:
    """组装上传到 AI 音乐工具的提示词。"""
    return f"风格：{mood}；主题：{theme}；请创作一首 {theme} 的流行音乐，节奏明快，情感真挚。"


def build_full_workflow(
    theme: str = "励志",
    mood: str = "轻快",
    lines: int = 8,
    title: Optional[str] = None,
) -> dict:
    """一次性生成歌词 + 占位音乐，返回文件路径信息。"""
    lyrics = generate_lyrics(theme=theme, lines=lines)
    lyrics_path = save_lyrics(lyrics)
    title = title or f"{theme}_{mood}_{random.randint(1000,9999)}"
    music_path = generate_music_placeholder(title=title)
    return {
        "title": title,
        "theme": theme,
        "mood": mood,
        "prompt": build_prompt(theme, mood),
        "lyrics": lyrics,
        "lyrics_path": lyrics_path,
        "music_path": music_path,
    }
