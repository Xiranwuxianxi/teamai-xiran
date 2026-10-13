#!/usr/bin/env python3
"""Read-only local preflight for book-sales-video; never prints secret values."""

from __future__ import annotations
import argparse, importlib.util, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
HOME = Path.home()
APP = Path("/Applications/OpenChatCut.app")
BRIDGE = SKILL_DIR / "scripts" / "openchatcut_mcp.py"
DOUBAO_KEYCHAIN_SERVICE = "codex.ai-self-media-video.DOUBAO_API_KEY"

def skill_name(path: Path) -> str | None:
    try: text = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    except OSError: return None
    match = re.search(r"(?m)^name:\s*[\"']?([^\"'\n]+)", text)
    return match.group(1).strip() if match else None

def find_skill(name: str) -> str | None:
    for root in (HOME/".codex/skills", HOME/".agents/skills", HOME/".claude/skills"):
        if not root.exists(): continue
        for path in [root/name/"SKILL.md", root/"WeChatReading/skills/SKILL.md", *root.glob("*/SKILL.md")]:
            if path.is_file() and skill_name(path) == name: return str(path)
    return None

def secret_available(name: str, service: str | None = None) -> bool:
    if os.environ.get(name, "").strip(): return True
    if platform.system() != "Darwin" or not service or not shutil.which("security"): return False
    result = subprocess.run(["security", "find-generic-password", "-s", service, "-w"], capture_output=True, text=True, timeout=8, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())

def run_json(command: list[str], timeout: int = 20) -> tuple[dict[str, Any] | None, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    raw = result.stdout.strip() or result.stderr.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw[-500:]
    return data, "" if result.returncode == 0 else raw[-500:]

def lark_status(profile: str, base_url: str, script_field: str) -> dict[str, Any]:
    binary = shutil.which("lark-cli")
    if not binary:
        return {"status": "missing", "valueExposed": False}
    cli = [binary, *(["--profile", profile] if profile else [])]
    whoami, error = run_json([*cli, "whoami"])
    if not whoami or not whoami.get("available") or whoami.get("tokenStatus") != "ready":
        return {"status": "profile-not-ready", "profile": profile or "default", "detail": error or "profile unavailable", "valueExposed": False}
    report: dict[str, Any] = {
        "status": "ready-no-base-check" if not base_url else "checking-base",
        "profile": profile or "default",
        "identity": whoami.get("identity"),
        "valueExposed": False,
    }
    if not base_url:
        return report
    resolved, error = run_json([*cli, "base", "+url-resolve", "--url", base_url, "--as", "bot"])
    if not resolved or not resolved.get("ok"):
        return {**report, "status": "base-url-or-permission-error", "detail": error or "URL resolve failed"}
    data = resolved.get("data", {})
    base_token, table_id = data.get("base_token"), data.get("block_id")
    if not base_token or not table_id:
        return {**report, "status": "base-url-unresolved"}
    fields, error = run_json([
        *cli, "base", "+field-list",
        "--base-token", str(base_token), "--table-id", str(table_id), "--as", "bot",
    ])
    if not fields or not fields.get("ok"):
        return {**report, "status": "base-permission-error", "detail": error or "field list failed"}
    names = [item.get("name") for item in fields.get("data", {}).get("fields", [])]
    return {**report, "status": "ready" if script_field in names else "script-field-missing", "scriptFieldFound": script_field in names}

def openchatcut_runtime() -> dict[str, Any]:
    if not APP.exists(): return {"status": "missing", "appPath": str(APP)}
    result = subprocess.run([sys.executable, str(BRIDGE), "--no-launch", "status"], capture_output=True, text=True, timeout=10, check=False)
    data: dict[str, Any] = {"status": "installed-not-running", "appPath": str(APP)}
    if result.returncode == 0:
        try: data.update(json.loads(result.stdout))
        except json.JSONDecodeError: pass
    return data

def carousel_status() -> dict[str, Any]:
    path = SKILL_DIR/"assets/carousel/manifest.json"; directory = "covers"
    try: directory = str(json.loads(path.read_text())["directory"])
    except Exception: pass
    folder = path.parent/directory; exts={".png",".jpg",".jpeg",".webp",".avif"}
    files = sorted(p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts) if folder.is_dir() else []
    return {"status":"available" if files else "empty", "directory":str(folder), "count":len(files), "files":files}

def build_report(base_url: str = "", lark_profile: str = "", script_field: str = "文案仿写.输出结果") -> dict[str, Any]:
    weread=find_skill("weread-skills"); runtime=openchatcut_runtime(); requests_ok=importlib.util.find_spec("requests") is not None
    voice_ok=requests_ok and secret_available("DOUBAO_API_KEY", DOUBAO_KEYCHAIN_SERVICE) and bool(os.getenv("DOUBAO_TTS_RESOURCE_ID")) and bool(os.getenv("DOUBAO_TTS_SPEAKER"))
    lark=lark_status(lark_profile, base_url, script_field)
    actions=[]
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): actions.append("安装 FFmpeg：macOS 可运行 brew install ffmpeg；其他系统使用系统包管理器")
    if not requests_ok: actions.append("安装 Python requests：python3 -m pip install requests")
    if not weread: actions.append("安装微信读书 Skill: npx skills add Tencent/WeChatReading -g")
    if not os.getenv("WEREAD_API_KEY"): actions.append("按 weread-skills 的说明申请并安全配置 WEREAD_API_KEY")
    if not os.getenv("PEXELS_API_KEY"): actions.append("从 https://www.pexels.com/api/ 申请并配置 PEXELS_API_KEY")
    if runtime["status"] == "missing": actions.append("从 https://github.com/0xsline/OpenChatCut/releases 安装 OpenChatCut Desktop；macOS 放入 /Applications")
    elif runtime["status"] != "ready": actions.append("运行装配命令时由本地桥接脚本自动启动 OpenChatCut")
    if not voice_ok: actions.append("配置豆包 TTS 的 API Key、resource ID 与 speaker；密钥不要写入任务目录")
    if lark["status"] == "missing": actions.append("安装飞书官方 CLI：npx @larksuite/cli@latest install")
    elif lark["status"] == "profile-not-ready": actions.append("配置飞书应用：lark-cli config init --new；如使用命名配置，再通过 --lark-profile 指定")
    elif lark["status"] in {"base-permission-error", "base-url-or-permission-error"}: actions.append("为企业应用开通 base:field:read、base:record:read、base:table:read、base:view:read，并把机器人加入目标 Base 协作者")
    elif lark["status"] == "script-field-missing": actions.append(f"确认目标表存在文案字段：{script_field}")
    return {"skill":"book-sales-video","checks":{"openchatcut":runtime,"wereadSkill":{"status":"ok" if weread else "missing","path":weread},"wereadApiKey":{"status":"configured" if os.getenv("WEREAD_API_KEY") else "missing","valueExposed":False},"pexels":{"apiKey":"configured" if os.getenv("PEXELS_API_KEY") else "missing","valueExposed":False},"voiceover":{"route":"Doubao direct TTS then local OpenChatCut import","status":"ready" if voice_ok else "missing-configuration","valueExposed":False},"larkBase":lark,"carouselAssets":carousel_status(),"localMediaTools":{"ffmpeg":shutil.which("ffmpeg"),"ffprobe":shutil.which("ffprobe")}},"gates":{"researchReady":bool(weread and os.getenv("WEREAD_API_KEY")),"openchatcutReady":runtime["status"] in {"ready","installed-not-running"},"doubaoReady":voice_ok,"larkReady":lark["status"] in {"ready", "ready-no-base-check"},"runtimeChecksPending":["OpenChatCut required tool surface","Codex image_gen"]},"actions":actions}

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--base-url",default="",help="可选：实测飞书 Base URL 与字段读取权限")
    parser.add_argument("--lark-profile",default="")
    parser.add_argument("--script-field",default="文案仿写.输出结果")
    args=parser.parse_args(); report=build_report(args.base_url,args.lark_profile,args.script_field)
    if args.json: print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        print("图书带货视频 Skill 环境检查")
        for key,value in report["checks"].items(): print(f"- {key}: {value.get('status','已检查') if isinstance(value,dict) else value}")
        for action in report["actions"]: print(f"  - {action}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
