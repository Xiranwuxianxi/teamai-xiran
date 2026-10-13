#!/usr/bin/env python3
"""Generate one cached narration file with Doubao TTS without exposing secrets.

The command accepts the complete script once. Long input is split internally at
sentence boundaries, synthesized with retries, trimmed, and merged into one WAV.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import platform
import subprocess
import time
import uuid
import wave
from pathlib import Path
from typing import Any

import requests


ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
KEYCHAIN_SERVICE = "codex.ai-self-media-video.DOUBAO_API_KEY"
DEFAULT_MAX_CHUNK_BYTES = 900
DEFAULT_JOIN_PAUSE_MS = 180
ALIGNMENT_VERSION = 2
SENTENCE_ENDINGS = set("。！？!?；;\n")


def load_api_key(env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value and env_name == "DOUBAO_API_KEY" and platform.system() == "Darwin":
        result = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
    if not value:
        raise SystemExit(
            f"Missing {env_name}. Use a secret-safe environment or macOS Keychain service "
            f"{KEYCHAIN_SERVICE}; never put the key in this project."
        )
    return value


def decode_events(raw: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    cursor = 0
    events: list[dict[str, Any]] = []
    while cursor < len(raw):
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1
        if cursor >= len(raw):
            break
        item, cursor = decoder.raw_decode(raw, cursor)
        if isinstance(item, dict):
            events.append(item)
    return events


def cache_key(text: str, resource_id: str, speaker: str, speech_rate: int, sample_rate: int,
              suffix: str, max_chunk_bytes: int, join_pause_ms: int) -> str:
    payload = json.dumps({"alignment_version": ALIGNMENT_VERSION, "text": text, "resource_id": resource_id, "speaker": speaker,
                          "speech_rate": speech_rate, "sample_rate": sample_rate, "suffix": suffix,
                          "max_chunk_bytes": max_chunk_bytes, "join_pause_ms": join_pause_ms},
                         ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def request_once(api_key: str, text: str, output: Path, resource_id: str, speaker: str,
                 speech_rate: int, sample_rate: int) -> tuple[bytes, dict[str, str]]:
    headers = {"X-Api-Key": api_key, "X-Api-Resource-Id": resource_id,
               "X-Api-Request-Id": str(uuid.uuid4()), "Content-Type": "application/json"}
    body = {"user": {"uid": "codex-book-sales-video"}, "req_params": {
        "text": text, "speaker": speaker,
        "audio_params": {"format": output.suffix.lstrip(".") or "wav", "sample_rate": sample_rate,
                         "speech_rate": speech_rate, "loudness_rate": 0}}}
    response = requests.post(ENDPOINT, headers=headers, json=body, timeout=180)
    if response.status_code == 429 or response.status_code >= 500:
        raise requests.HTTPError(f"retryable HTTP {response.status_code}", response=response)
    try:
        events = decode_events(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Doubao TTS returned unreadable data (HTTP {response.status_code})") from exc
    chunks: list[bytes] = []
    provider_error: dict[str, Any] | None = None
    for event in events:
        if isinstance(event.get("data"), str):
            chunks.append(base64.b64decode(event["data"]))
        code = event.get("code") or event.get("header", {}).get("code")
        if code and code != 20000000 and provider_error is None:
            provider_error = event
    if not chunks:
        safe_error = {key: provider_error.get(key) for key in ("code", "message") if key in provider_error} if provider_error else None
        raise RuntimeError(f"Doubao TTS produced no audio (HTTP {response.status_code}, error={safe_error})")
    return b"".join(chunks), {"x_tt_logid": response.headers.get("X-Tt-Logid", "")}


def split_text(text: str, max_bytes: int) -> list[str]:
    """Split into sentence-sized TTS units, never just transport-sized chunks.

    One script invocation still produces one merged WAV, but each returned unit
    has a measured PCM duration. Those measurements are the subtitle/timeline
    alignment source and avoid depending on editor ASR.
    """
    if max_bytes < 100:
        raise ValueError("max chunk bytes must be at least 100")
    sentences: list[str] = []
    buffer: list[str] = []
    for char in text:
        buffer.append(char)
        if char in SENTENCE_ENDINGS:
            piece = "".join(buffer).strip()
            if piece:
                sentences.append(piece)
            buffer = []
    tail = "".join(buffer).strip()
    if tail:
        sentences.append(tail)

    units: list[str] = []
    for sentence in sentences:
        if len(sentence.encode("utf-8")) <= max_bytes:
            units.append(sentence)
            continue
        start = 0
        while start < len(sentence):
            end = start
            byte_count = 0
            while end < len(sentence):
                char_bytes = len(sentence[end].encode("utf-8"))
                if byte_count + char_bytes > max_bytes:
                    break
                byte_count += char_bytes
                end += 1
            if end == start:
                raise ValueError("single UTF-8 character exceeds max chunk size")
            units.append(sentence[start:end].strip())
            start = end
    return units


def trim_pcm16(pcm: bytes, channels: int, sample_rate: int) -> bytes:
    """Trim only obvious edge silence and keep 45 ms of breathing room."""
    if not pcm:
        return pcm
    frame_width = channels * 2
    frame_count = len(pcm) // frame_width
    window_frames = max(1, sample_rate // 100)
    threshold = 220

    def window_peak(first_frame: int) -> int:
        block = pcm[first_frame * frame_width:min(frame_count, first_frame + window_frames) * frame_width]
        samples = memoryview(block).cast("h")
        return max((abs(value) for value in samples), default=0)

    first = 0
    while first < frame_count and window_peak(first) < threshold:
        first += window_frames
    last = frame_count
    while last > first and window_peak(max(first, last - window_frames)) < threshold:
        last -= window_frames
    pad = int(sample_rate * 0.045)
    first = max(0, first - pad)
    last = min(frame_count, last + pad)
    return pcm[first * frame_width:last * frame_width]


def merge_wavs(audio_chunks: list[bytes], join_pause_ms: int) -> tuple[bytes, list[int], int]:
    parameters: tuple[int, int, int, str] | None = None
    pcm_chunks: list[bytes] = []
    for raw in audio_chunks:
        with wave.open(io.BytesIO(raw), "rb") as source:
            current = (source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype())
            if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                raise RuntimeError("Doubao multi-chunk merge requires uncompressed 16-bit WAV output")
            if parameters is None:
                parameters = current
            elif current != parameters:
                raise RuntimeError("Doubao returned incompatible WAV parameters between chunks")
            pcm_chunks.append(trim_pcm16(source.readframes(source.getnframes()), current[0], current[2]))
    if parameters is None:
        raise RuntimeError("No WAV chunks to merge")
    channels, sample_width, sample_rate, _ = parameters
    silence = b"\x00" * (int(sample_rate * join_pause_ms / 1000) * channels * sample_width)
    trimmed_frame_counts = [len(chunk) // (channels * sample_width) for chunk in pcm_chunks]
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(channels)
        target.setsampwidth(sample_width)
        target.setframerate(sample_rate)
        target.writeframes(silence.join(pcm_chunks))
    return output.getvalue(), trimmed_frame_counts, sample_rate


def request_with_retry(api_key: str, text: str, output: Path, resource_id: str, speaker: str,
                       speech_rate: int, sample_rate: int, retries: int) -> tuple[bytes, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return request_once(api_key, text, output, resource_id, speaker, speech_rate, sample_rate)
        except requests.HTTPError as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(8, 2 ** (attempt - 1)))
    raise RuntimeError(f"Doubao TTS failed after {retries} attempts: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resource-id", default=os.environ.get("DOUBAO_TTS_RESOURCE_ID", ""))
    parser.add_argument("--speaker", default=os.environ.get("DOUBAO_TTS_SPEAKER", ""))
    parser.add_argument("--speech-rate", type=int, default=0)
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--api-key-env", default="DOUBAO_API_KEY")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--max-chunk-bytes", type=int, default=DEFAULT_MAX_CHUNK_BYTES)
    parser.add_argument("--join-pause-ms", type=int, default=DEFAULT_JOIN_PAUSE_MS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    text = text.strip()
    if not text or not args.resource_id.strip() or not args.speaker.strip():
        raise SystemExit("Narration text, --resource-id, and --speaker are required.")
    if args.output.suffix.lower() != ".wav":
        raise SystemExit("book-sales-video narration output must be a .wav file")
    if not 80 <= args.join_pause_ms <= 450:
        raise SystemExit("--join-pause-ms must be between 80 and 450")
    chunks = split_text(text, args.max_chunk_bytes)
    key = cache_key(text, args.resource_id, args.speaker, args.speech_rate, args.sample_rate,
                    args.output.suffix, args.max_chunk_bytes, args.join_pause_ms)
    report = args.report or args.output.with_suffix(args.output.suffix + ".json")
    if args.output.is_file() and report.is_file() and not args.force:
        existing = json.loads(report.read_text(encoding="utf-8"))
        if existing.get("cache_key") == key and args.output.stat().st_size > 0:
            existing["cache_hit"] = True
            print(json.dumps(existing, ensure_ascii=False, indent=2))
            return 0
    api_key = load_api_key(args.api_key_env)
    audio_parts: list[bytes] = []
    provider_log_ids: list[str] = []
    for chunk in chunks:
        part, provider_meta = request_with_retry(
            api_key, chunk, args.output, args.resource_id, args.speaker,
            args.speech_rate, args.sample_rate, args.retries,
        )
        audio_parts.append(part)
        if provider_meta.get("x_tt_logid"):
            provider_log_ids.append(provider_meta["x_tt_logid"])
    audio, trimmed_frame_counts, actual_sample_rate = merge_wavs(audio_parts, args.join_pause_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio)
    cursor_frames = 0
    join_frames = int(actual_sample_rate * args.join_pause_ms / 1000)
    alignment_segments: list[dict[str, Any]] = []
    for index, (chunk, frame_count) in enumerate(zip(chunks, trimmed_frame_counts), start=1):
        start_ms = round(cursor_frames * 1000 / actual_sample_rate, 3)
        end_frame = cursor_frames + frame_count
        end_ms = round(end_frame * 1000 / actual_sample_rate, 3)
        pause_after = args.join_pause_ms if index < len(chunks) else 0
        alignment_segments.append({
            "id": f"tts-unit-{index:03d}", "text": chunk, "startMs": start_ms,
            "endMs": end_ms, "durationMs": round((end_frame - cursor_frames) * 1000 / actual_sample_rate, 3),
            "joinPauseAfterMs": pause_after, "requestIndex": index,
        })
        cursor_frames = end_frame + (join_frames if index < len(chunks) else 0)
    result = {"output": str(args.output), "audio_bytes": len(audio), "cache_key": key, "cache_hit": False,
              "provider": "doubao-direct-v3", "endpoint": ENDPOINT, "resource_id": args.resource_id,
              "speaker": args.speaker, "speech_rate": args.speech_rate, "sample_rate": args.sample_rate,
              "workflow_invocations": 1, "provider_request_count": len(chunks),
              "chunk_text_bytes": [len(chunk.encode("utf-8")) for chunk in chunks],
              "join_pause_ms": args.join_pause_ms, "edge_silence_trimmed": True,
              "alignment": {"version": ALIGNMENT_VERSION, "method": "trimmed-pcm-duration-plus-fixed-join-pause",
                            "unitCount": len(alignment_segments), "sampleRate": actual_sample_rate,
                            "segments": alignment_segments},
              "x_tt_logids": provider_log_ids}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
