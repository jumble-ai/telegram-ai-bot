from __future__ import annotations

import wave
from dataclasses import dataclass
from io import BytesIO
from typing import Any, cast

import av
from av.audio.resampler import AudioResampler
from av.container.input import InputContainer


class AudioConversionError(RuntimeError):
    """Raised when audio cannot be converted."""


@dataclass(frozen=True, slots=True)
class ConvertedAudio:
    """Converted audio bytes and format."""

    content: bytes
    format: str


def convert_ogg_opus_to_wav(audio: bytes) -> ConvertedAudio:
    """Convert Telegram OGG/Opus voice bytes to WAV using PyAV."""
    try:
        container = cast(InputContainer, av.open(BytesIO(audio)))
        stream = next(stream for stream in container.streams if stream.type == "audio")
    except Exception as error:
        msg = "Cannot open OGG/Opus audio."
        raise AudioConversionError(msg) from error

    sample_rate = 16_000
    resampler = AudioResampler(format="s16", layout="mono", rate=sample_rate)
    pcm_chunks: list[bytes] = []

    try:
        for packet in container.demux(stream):
            for frame in packet.decode():
                for converted_frame in _resample_frame(resampler, frame):
                    pcm_chunks.append(bytes(converted_frame.planes[0]))
    except Exception as error:
        msg = "Cannot decode OGG/Opus audio."
        raise AudioConversionError(msg) from error
    finally:
        container.close()

    if not pcm_chunks:
        raise AudioConversionError("Decoded audio is empty.")

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(pcm_chunks))

    return ConvertedAudio(content=wav_buffer.getvalue(), format="wav")


def _resample_frame(
    resampler: AudioResampler,
    frame: Any,
) -> list[Any]:
    result = resampler.resample(frame)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [cast(Any, result)]
