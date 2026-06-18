"""
配置模块 - 配置与代码分离
"""
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 音质配置 (bitrate)
QUALITY = {
    "high": {"ytdlp_format": "bestaudio/best", "ffmpeg_bitrate": "320k"},
    "mid":  {"ytdlp_format": "bestaudio/best", "ffmpeg_bitrate": "192k"},
    "low":  {"ytdlp_format": "worstaudio/worst", "ffmpeg_bitrate": "96k"},
}

# 默认音质
DEFAULT_QUALITY = "mid"

# 输出目录
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件
LOG_FILE = LOG_DIR / "yt2mp3.log"

# 临时文件目录
TEMP_DIR = BASE_DIR / ".temp"
TEMP_DIR.mkdir(exist_ok=True)

# yt-dlp 默认参数
YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
}
