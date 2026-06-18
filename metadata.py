"""
元数据模块 - 使用 mutagen 嵌入 ID3 标签
"""
import logging
from pathlib import Path

from mutagen.id3 import (
    ID3, TIT2, TPE1, TALB, APIC, TPOS, TRCK, TDRC, TCON,
)
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)


def extract_info(url: str) -> dict:
    """
    通过 yt-dlp 提取视频元信息（不下视频）。
    
    Args:
        url: YouTube 视频 URL
        
    Returns:
        包含标题、上传者、封面等的字典
    """
    import json
    import subprocess

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.warning("无法获取视频元信息: %s", result.stderr.strip() or result.stdout.strip())
        return {}

    data = json.loads(result.stdout.strip().split("\n")[0])
    info = {
        "title": data.get("title", ""),
        "uploader": data.get("uploader", ""),
        "album": data.get("album", data.get("playlist_title", "")),
        "thumbnail": data.get("thumbnail", ""),
        "upload_date": data.get("upload_date", ""),
    }
    logger.info("获取元数据: title=%s, uploader=%s", info["title"], info["uploader"])
    return info


def embed_metadata(mp3_path: Path, info: dict) -> None:
    """
    向 MP3 文件嵌入 ID3 标签。
    
    Args:
        mp3_path: MP3 文件路径
        info: 元数据字典 (title, uploader, album, thumbnail, upload_date)
    """
    if not mp3_path.exists():
        logger.warning("文件不存在，跳过元数据嵌入: %s", mp3_path)
        return

    try:
        audio = MP3(mp3_path, ID3=ID3)
    except Exception:
        audio = MP3(mp3_path)

    # 确保有 ID3 标签容器
    if audio.tags is None:
        audio.add_tags()

    # 标题
    if info.get("title"):
        audio.tags.add(TIT2(encoding=3, text=info["title"]))

    # 艺术家（上传者）
    if info.get("uploader"):
        audio.tags.add(TPE1(encoding=3, text=info["uploader"]))

    # 专辑
    if info.get("album"):
        audio.tags.add(TALB(encoding=3, text=info["album"]))
    elif info.get("uploader"):
        audio.tags.add(TALB(encoding=3, text=info["uploader"]))

    # 上传日期
    if info.get("upload_date"):
        date_str = info["upload_date"]
        if len(date_str) == 8:
            formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            audio.tags.add(TDRC(encoding=3, text=formatted))

    # 封面图
    if info.get("thumbnail"):
        _embed_cover(audio, info["thumbnail"])

    audio.save()
    logger.info("元数据嵌入完成: %s", mp3_path.name)


def _embed_cover(audio: MP3, thumbnail_url: str) -> None:
    """下载并嵌入封面图"""
    import requests

    try:
        resp = requests.get(thumbnail_url, timeout=15)
        resp.raise_for_status()
        image_data = resp.content

        # 判断 MIME 类型
        mime = resp.headers.get("Content-Type", "image/jpeg")
        # 根据实际数据修正
        if image_data[:4] == b"\x89PNG":
            mime = "image/png"
        elif image_data[:2] in (b"\xFF\xD8",):
            mime = "image/jpeg"
        elif image_data[:6] in (b"GIF87a", b"GIF89a"):
            mime = "image/gif"
        elif image_data[:4] == b"WEBP":
            mime = "image/webp"

        apic_type = {
            "image/jpeg": 3,
            "image/png": 3,
            "image/gif": 3,
            "image/webp": 3,
        }.get(mime, 3)

        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime,
                type=apic_type,
                desc="Cover",
                data=image_data,
            )
        )
        logger.info("封面图已嵌入 (%s, %d bytes)", mime, len(image_data))
    except Exception as e:
        logger.warning("封面图嵌入失败: %s", e)
