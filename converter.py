"""
转换模块 - 将音频转换为 MP3

优先使用 ffmpeg 编码；若 ffmpeg 不支持 mp3，则降级使用 lameenc。
"""
import logging
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _convert_via_ffmpeg(input_path: Path, output_path: Path, bitrate: str) -> bool:
    """尝试使用 ffmpeg 自带的 mp3 编码器。"""
    # 尝试多种可能的 mp3 编码器
    for codec in ["libmp3lame", "mp3", "mp3float"]:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-codec:a", codec,
            "-b:a", bitrate,
            "-y",
            "-loglevel", "error",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True
    return False


def _convert_via_lameenc(input_path: Path, output_path: Path, bitrate_kbps: int) -> None:
    """使用 lameenc Python 库编码 MP3。"""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import lameenc

    import wave

    with wave.open(str(input_path), "rb") as wav:
        frames = wav.readframes(wav.getnframes())
        params = wav.getparams()

    encoder = lameenc.Encoder()
    encoder.set_channels(params.nchannels)
    encoder.set_in_sample_rate(params.framerate)
    encoder.set_bit_rate(bitrate_kbps)
    encoder.set_quality(2)

    mp3_data = encoder.encode(frames)
    mp3_data += encoder.flush()

    output_path.write_bytes(mp3_data)


def convert_to_mp3(input_path: Path, quality: str = config.DEFAULT_QUALITY) -> Path:
    """
    将音频文件转换为 MP3 格式。
    
    Args:
        input_path: 输入音频文件路径
        quality: 音质等级 (high/mid/low)
        
    Returns:
        输出的 MP3 文件路径
        
    Raises:
        RuntimeError: 转换失败时抛出
    """
    quality_cfg = config.QUALITY.get(quality, config.QUALITY[config.DEFAULT_QUALITY])
    output_path = config.OUTPUT_DIR / f"{input_path.stem}.mp3"

    # 避免覆盖，如果存在则加序号
    counter = 1
    while output_path.exists():
        output_path = config.OUTPUT_DIR / f"{input_path.stem}_{counter}.mp3"
        counter += 1

    logger.info("转换 MP3: %s -> %s", input_path.name, output_path.name)

    # 策略 1：尝试 ffmpeg
    bitrate = quality_cfg["ffmpeg_bitrate"]
    if _convert_via_ffmpeg(input_path, output_path, bitrate):
        logger.info("ffmpeg 转换成功")
    else:
        # 策略 2：降级到 lameenc（需要先将任意输入转成 WAV）
        logger.info("ffmpeg mp3 编码不可用，降级到 lameenc")
        wav_path = input_path
        # 如果不是 WAV，先转 WAV
        if input_path.suffix.lower() not in (".wav",):
            wav_path = config.TEMP_DIR / f"{input_path.stem}_temp.wav"
            subprocess.run(
                ["ffmpeg", "-i", str(input_path), "-y", "-loglevel", "error", str(wav_path)],
                capture_output=True, text=True, timeout=300,
            )
        bitrate_kbps = int(bitrate.replace("k", ""))
        _convert_via_lameenc(wav_path, output_path, bitrate_kbps)
        # 清理临时 WAV
        if wav_path != input_path and wav_path.exists():
            wav_path.unlink()

    if not output_path.exists():
        raise RuntimeError(f"转换后文件不存在: {output_path}")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("转换完成: %s (%.1f MB)", output_path.name, size_mb)
    return output_path
