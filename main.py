"""
Yt2Mp3 - YouTube 转 MP3 工具

用法:
    python main.py <YouTube_URL> [--quality high|mid|low]
    python main.py <YouTube_URL> -q high

示例:
    python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
    python main.py https://youtu.be/dQw4w9WgXcQ -q high
"""
import argparse
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from logger import setup_logger
from downloader import download_audio
from converter import convert_to_mp3
from metadata import extract_info, embed_metadata
from cleaner import clean_temp

logger = setup_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Yt2Mp3 - 将 YouTube 视频转换为 MP3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python main.py https://www.youtube.com/watch?v=xxx\n  python main.py https://youtu.be/xxx -q high",
    )
    parser.add_argument("url", help="YouTube 视频 URL")
    parser.add_argument(
        "-q", "--quality",
        choices=["high", "mid", "low"],
        default=config.DEFAULT_QUALITY,
        help=f"音质等级 (默认: {config.DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="不嵌入元数据",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="保留临时文件（用于调试）",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info("=" * 50)
    logger.info("Yt2Mp3 开始处理: %s", args.url)
    logger.info("音质: %s, 嵌入元数据: %s", args.quality, not args.no_meta)

    temp_audio = None
    try:
        # Step 1: 下载音频
        logger.info("[1/3] 正在下载音频...")
        temp_audio = download_audio(args.url, args.quality)
        logger.info("  ✅ 下载完成: %s", temp_audio.name)

        # Step 2: 转换为 MP3
        logger.info("[2/3] 正在转换 MP3...")
        mp3_path = convert_to_mp3(temp_audio, args.quality)
        logger.info("  ✅ 转换完成: %s", mp3_path.name)

        # Step 3: 嵌入元数据
        if not args.no_meta:
            logger.info("[3/3] 正在获取并嵌入元数据...")
            info = extract_info(args.url)
            embed_metadata(mp3_path, info)
            logger.info("  ✅ 元数据嵌入完成")
        else:
            logger.info("[3/3] 跳过元数据嵌入 (--no-meta)")

        # 输出结果
        file_size = mp3_path.stat().st_size / (1024 * 1024)
        logger.info("=" * 50)
        logger.info("🎵 生成成功!")
        logger.info("   📁 文件: %s", mp3_path)
        logger.info("   📏 大小: %.1f MB", file_size)
        logger.info("   🔊 音质: %s", args.quality)
        print(f"\n🎵 {mp3_path.name} ({file_size:.1f} MB)")

    except Exception as e:
        logger.error("❌ 处理失败: %s", e, exc_info=logger.isEnabledFor(10))
        sys.exit(1)

    finally:
        # 清理临时文件
        if temp_audio and not args.keep_temp:
            clean_temp(temp_audio)
            logger.debug("临时文件已清理")


if __name__ == "__main__":
    main()
