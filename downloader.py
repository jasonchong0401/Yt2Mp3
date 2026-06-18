"""
下载模块 - 使用 yt-dlp 下载 YouTube 音频
"""
import logging
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def download_audio(url: str, quality: str = config.DEFAULT_QUALITY) -> Path:
    """
    下载 YouTube 视频的音频流，返回临时音频文件路径。
    
    Args:
        url: YouTube 视频 URL
        quality: 音质等级 (high/mid/low)
        
    Returns:
        下载后的临时音频文件路径
        
    Raises:
        RuntimeError: 下载失败时抛出
    """
    quality_cfg = config.QUALITY.get(quality, config.QUALITY[config.DEFAULT_QUALITY])
    temp_template = str(config.TEMP_DIR / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",                                   # 只提取音频
        "--audio-format", "m4a",                # 输出 m4a (aac) 格式，方便 ffmpeg 处理
        "-f", quality_cfg["ytdlp_format"],      # 音质选择
        "-o", temp_template,                    # 输出模板
        "--no-playlist",                        # 不处理播放列表
        "--print", "filename",                  # 输出实际文件名
        "--rm-cache-dir",
        url,
    ]

    logger.info("下载音频: %s", url)
    logger.debug("执行命令: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip() or "未知错误"
        logger.error("下载失败: %s", error_msg)
        raise RuntimeError(f"下载失败: {error_msg}")

    # 从输出中获取实际文件名
    output_lines = [line.strip() for line in result.stdout.split("\n") if line.strip()]
    if not output_lines:
        raise RuntimeError("下载成功但无法获取输出文件路径")

    audio_path = Path(output_lines[-1])
    if not audio_path.exists():
        raise RuntimeError(f"下载后文件不存在: {audio_path}")

    logger.info("下载完成: %s", audio_path)
    return audio_path
