# Runtime contract

Use this reference when preparing a machine for the skill or diagnosing a missing Docker runtime.

## Host requirements

- Codex with the built-in `image_gen` tool for still-frame generation.
- Docker, FFmpeg, ffprobe, Python 3, and ripgrep.
- The open-source [HBG Gemini Flow Suite](https://github.com/Mr-funny/hbg-gemini-flow-suite), running as a container named `gemini-flow-suite`.
- A workspace bind-mounted read-only at `/workspace` inside the container.
- A writable output mount at `/data/outputs` inside the container and at `outputs/gemini-flow-suite` in the host workspace.

Run `scripts/check_prerequisites.sh` from the active project before generating media.

## Container requirements

The container must provide:

- `/opt/gemini-venv/bin/python` with `gemini_webapi` installed.
- A pre-authorized Gemini cookie file at `/data/auth/gemini/cookies.json`.
- `veo-watermark-remover` when optional white sparkle cleanup is requested.

The skill never reads or prints cookie values. Authorization is a separate one-time user-controlled setup. Actual poem-video generation must use Docker commands and must not open or control the host browser.

## Setup outline

```bash
git clone https://github.com/Mr-funny/hbg-gemini-flow-suite.git
cd hbg-gemini-flow-suite
cp .env.example .env
docker compose up -d --build
./suite auth gemini
```

Follow the runtime repository's README for current authorization and mount configuration. Never commit `.env`, cookies, Chrome profiles, exported Docker volumes, generated media, or provider credentials.

## Optional watermark cleanup

Only remove the provider's white sparkle/diamond overlay when the user requests it and applicable terms permit it. Preserve traditional red seals and intentional painting marks. Skip this step when the cleanup tool is unavailable or inappropriate; report the limitation rather than silently altering another region.
