"""
清理模块 - 清理临时文件
"""
import logging
import shutil
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def clean_temp(file_path: Path) -> None:
    """
    清理单个临时文件或目录。
    
    Args:
        file_path: 要清理的文件或目录路径
    """
    if not file_path.exists():
        return

    try:
        if file_path.is_file() or file_path.is_symlink():
            file_path.unlink(missing_ok=True)
            logger.debug("已删除临时文件: %s", file_path)
        elif file_path.is_dir():
            shutil.rmtree(file_path, ignore_errors=True)
            logger.debug("已删除临时目录: %s", file_path)
    except Exception as e:
        logger.warning("清理失败 %s: %s", file_path, e)


def clean_temp_dir() -> None:
    """清空临时文件目录中的所有文件"""
    if config.TEMP_DIR.exists():
        for item in config.TEMP_DIR.iterdir():
            clean_temp(item)
        logger.info("临时目录已清空")
