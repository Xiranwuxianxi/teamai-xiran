#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from gemini_webapi import GeminiClient


def load_cookie_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("cookieMap"), dict):
        data = data["cookieMap"]
    elif isinstance(data, list):
        data = {
            item.get("name"): item.get("value")
            for item in data
            if isinstance(item, dict) and item.get("name") and item.get("value")
        }
    if not isinstance(data, dict) or not data.get("__Secure-1PSID"):
        raise RuntimeError("Gemini cookie file is not authorized")
    return {str(key): str(value) for key, value in data.items() if value is not None}


async def main() -> int:
    image = Path(os.environ["POEM_I2V_IMAGE"])
    output = Path(os.environ["POEM_I2V_OUTPUT"])
    prompt = os.environ["POEM_I2V_PROMPT"]
    cookie_file = Path(os.environ.get("GEMINI_COOKIE_FILE", "/data/auth/gemini/cookies.json"))
    output.mkdir(parents=True, exist_ok=True)

    cookies = load_cookie_map(cookie_file)
    client = GeminiClient(
        cookies["__Secure-1PSID"],
        cookies.get("__Secure-1PSIDTS"),
        proxy=os.environ.get("HTTPS_PROXY") or None,
    )
    await client.init(
        timeout=900,
        auto_close=False,
        auto_refresh=True,
        refresh_interval=600,
        watchdog_timeout=180,
        verbose=False,
    )
    saved: list[dict[str, str | None]] = []
    try:
        response = await asyncio.wait_for(
            client.generate_content(prompt=prompt, files=[str(image)], temporary=False),
            timeout=900,
        )
        for index, video in enumerate(response.videos, start=1):
            item = await asyncio.wait_for(
                video.save(
                    path=str(output),
                    filename=f"poem-scene-{index}",
                    verbose=True,
                ),
                timeout=1200,
            )
            saved.append(item)
        if not saved:
            raise RuntimeError("Gemini returned no downloadable video")
        (output / "result.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "video_count": len(response.videos),
                    "saved": saved,
                    "response_text": response.text,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps(saved, ensure_ascii=False))
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
