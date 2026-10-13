#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


PUNCTUATION = re.compile(r"[，。！？、；：,.!?;:‘’“”\"'（）()【】《》〈〉\s]")


def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def clean_line(value: str) -> str:
    return PUNCTUATION.sub("", value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--line", action="append", required=True)
    parser.add_argument("--duration", type=float, default=9.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--font", default="Ma Shan Zheng")
    parser.add_argument("--interval", type=float, default=0.42)
    args = parser.parse_args()

    lines = [clean_line(value) for value in args.line if clean_line(value)]
    if not 1 <= len(lines) <= 2:
        raise SystemExit("Provide one or two non-empty --line values")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Poem,{args.font},112,&H00D8E3E8,&H00D8E3E8,&H683A3732,&H82171310,0,0,0,0,100,100,1,0,1,1.4,2.2,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events: list[str] = []
    x_positions = [920] if len(lines) == 1 else [925, 785]
    reveal_start = 0.55
    end = max(reveal_start + 0.5, args.duration - 0.25)
    for line_index, line in enumerate(lines):
        count = len(line)
        step_y = min(138.0, 1120.0 / max(1, count - 1))
        start_y = 300.0
        for char_index, char in enumerate(line):
            start = reveal_start + char_index * args.interval
            y = start_y + char_index * step_y
            events.append(
                "Dialogue: 0,"
                f"{ass_time(start)},{ass_time(end)},Poem,,0,0,0,,"
                f"{{\\pos({x_positions[line_index]},{round(y)})\\fad(240,420)\\blur0.7}}{char}"
            )
        reveal_start += count * args.interval + 0.30

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
