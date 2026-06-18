"""
日志模块 - 统一的日志配置
"""
import logging
import sys
from pathlib import Path

import config


def setup_logger() -> logging.Logger:
    """
    配置并返回根日志器。
    - 控制台: INFO 级别
    - 文件: DEBUG 级别（保留最近 3 个日志文件）
    """
    logger = logging.getLogger("yt2mp3")
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler - INFO 级别
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler - DEBUG 级别
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 日志轮转（保留最近3个文件）
    _rotate_logs(config.LOG_DIR, "yt2mp3.log", max_backups=3)

    return logger


def _rotate_logs(log_dir: Path, base_name: str, max_backups: int = 3) -> None:
    """简单的日志轮转"""
    log_file = log_dir / base_name
    if not log_file.exists():
        return

    import time
    backup = log_dir / f"{base_name}.{int(time.time())}"
    try:
        log_file.rename(backup)
    except OSError:
        pass

    # 删除旧的备份，只保留 max_backups 个
    backups = sorted(log_dir.glob(f"{base_name}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[max_backups:]:
        try:
            old.unlink()
        except OSError:
            pass
