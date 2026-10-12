#!/usr/bin/env python3
"""Small, dependency-free client for the Index Hub API.

The tool deliberately accepts only whitelisted relative paths and never prints local
configuration or authorization headers. Its JSON output is intended for
internal skill processing, not direct inclusion in a customer-facing answer.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import fcntl
import signal

# Ignore SIGPIPE so that writing to a consumer that has already closed its end
# raises BrokenPipeError instead of terminating the process. main() catches the
# exception and exits cleanly once the response has been persisted.
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)


# Preserve the lexical path of the invoking script to identify the owning skill.
SKILL_DIR = Path(os.path.abspath(__file__)).parents[1]
SKILL_NAME = SKILL_DIR.name
ALLOWED_PATHS = {
    "/skill/v2/discovery/hot-search",
    "/skill/v2/discovery/hot-search-recommend",
    "/skill/v2/index/detail",
    "/skill/v2/index/financial-indicators",
    "/skill/v2/index/holdings",
    "/skill/v2/index/return",
    "/skill/v2/index/valuation",
    "/skill/v2/quote/index",
    "/skill/v2/quote/index/kline",
    "/skill/v2/quote/minite",
    "/skill/v2/search/chinaIndex",
    "/skill/v2/search/index-by-stock",
}

CACHE_DIR_ENV = "INDEX_HUB_CACHE_DIR"
TURN_ID_ENV = "INDEX_HUB_TURN_ID"
TRACE_FILE_ENV = "INDEX_HUB_TRACE_FILE"


def load_config():
    config_path = SKILL_DIR / "config.py"
    spec = importlib.util.spec_from_file_location("index_hub_skill_config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载本地配置")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_json_object(raw: str | None, label: str) -> dict[str, Any]:
    if raw is None:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{label} 必须是 JSON 对象")
    return value


def validate_path(path: str) -> None:
    if not path.startswith("/") or "://" in path or ".." in path:
        raise ValueError("只允许调用相对路径（以 / 开头）")
    if path not in ALLOWED_PATHS:
        raise ValueError(f"接口不属于 {SKILL_NAME} 的能力范围")


def validate_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise RuntimeError("接口响应不是 JSON 对象")
    if result.get("success") is not True or result.get("code") not in (0, "0", "0000", None):
        message = str(result.get("message") or "业务请求失败").replace("\n", " ")[:200]
        raise RuntimeError(message)
    return result


def request_signature(
    method: str,
    path: str,
    query: dict[str, Any],
    body: dict[str, Any],
) -> str:
    signature_data = {
        "skill": SKILL_NAME,
        "method": method,
        "path": path,
        "query": query,
        "body": body,
    }
    encoded = json.dumps(
        signature_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_file_for(signature: str) -> Path | None:
    cache_dir = os.environ.get(CACHE_DIR_ENV, "").strip()
    turn_id = os.environ.get(TURN_ID_ENV, "").strip()
    if not cache_dir or not turn_id:
        return None
    if (
        len(turn_id) > 128
        or turn_id in {".", ".."}
        or Path(turn_id).name != turn_id
        or "\x00" in turn_id
    ):
        raise RuntimeError(f"{TURN_ID_ENV} 格式无效")
    return Path(cache_dir).expanduser() / turn_id / f"{signature}.json"


@contextlib.contextmanager
def request_lock(cache_file: Path) -> Iterator[None]:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file = cache_file.with_suffix(".lock")
    with lock_file.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_cached_result(cache_file: Path) -> dict[str, Any] | None:
    try:
        raw = cache_file.read_text(encoding="utf-8")
        return validate_result(json.loads(raw))
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeError):
        return None


def write_cached_result(cache_file: Path, result: dict[str, Any]) -> None:
    raw = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    temp_file = cache_file.with_name(
        f".{cache_file.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with temp_file.open("x", encoding="utf-8") as handle:
            os.chmod(temp_file, 0o600)
            handle.write(raw)
            handle.flush()
        temp_file.replace(cache_file)
    finally:
        try:
            temp_file.unlink()
        except FileNotFoundError:
            pass


def write_output_file(output_path: Path, result: dict[str, Any]) -> None:
    """Write the full JSON response to a user-specified path.

    The file is created with restrictive permissions (0o600) and replaced
    atomically so that consumers never see a partially-written JSON file.
    """
    raw = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    temp_file = output_path.with_name(
        f".{output_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with temp_file.open("x", encoding="utf-8") as handle:
            os.chmod(temp_file, 0o600)
            handle.write(raw)
            handle.flush()
        temp_file.replace(output_path)
    finally:
        try:
            temp_file.unlink()
        except FileNotFoundError:
            pass


def append_trace(
    *,
    signature: str,
    method: str,
    path: str,
    cache_hit: bool,
    network_request: bool,
    network_elapsed_ms: int,
    success: bool,
) -> None:
    trace_file_raw = os.environ.get(TRACE_FILE_ENV, "").strip()
    if not trace_file_raw:
        return
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "turn_id": os.environ.get(TURN_ID_ENV, ""),
        "skill": SKILL_NAME,
        "signature": signature,
        "method": method,
        "path": path,
        "cache_hit": cache_hit,
        "network_request": network_request,
        "network_elapsed_ms": network_elapsed_ms,
        "success": success,
    }
    payload = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    try:
        trace_file = Path(trace_file_raw).expanduser()
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(trace_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "ab") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(payload)
                handle.flush()
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        # Tracing is diagnostic and must not turn a successful data request
        # into a failed user answer.
        return


def request_once(
    config: Any,
    method: str,
    path: str,
    query: dict[str, Any],
    body: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    validate_path(path)
    url = config.BASE_URL.rstrip("/") + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if method != "GET" else None
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}",
            "X-Caller-Type": getattr(config, "CALLER_TYPE", "external"),
        },
    )
    with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return validate_result(json.loads(raw))


def request_api(
    config: Any,
    method: str,
    path: str,
    query: dict[str, Any],
    body: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    try:
        return request_once(config, method, path, query, body, timeout)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"HTTP 请求失败（状态码 {error.code}）") from None


def request_with_turn_cache(
    config: Any,
    method: str,
    path: str,
    query: dict[str, Any],
    body: dict[str, Any],
    timeout: float,
    refresh: bool = False,
) -> dict[str, Any]:
    validate_path(path)
    signature = request_signature(method, path, query, body)
    cache_file = cache_file_for(signature)

    def fetch() -> dict[str, Any]:
        started = time.monotonic()
        try:
            result = request_api(config, method, path, query, body, timeout)
        except Exception:
            append_trace(
                signature=signature,
                method=method,
                path=path,
                cache_hit=False,
                network_request=True,
                network_elapsed_ms=round((time.monotonic() - started) * 1000),
                success=False,
            )
            raise
        append_trace(
            signature=signature,
            method=method,
            path=path,
            cache_hit=False,
            network_request=True,
            network_elapsed_ms=round((time.monotonic() - started) * 1000),
            success=True,
        )
        return result

    if cache_file is None:
        return fetch()

    with request_lock(cache_file):
        if not refresh:
            cached = read_cached_result(cache_file)
            if cached is not None:
                append_trace(
                    signature=signature,
                    method=method,
                    path=path,
                    cache_hit=True,
                    network_request=False,
                    network_elapsed_ms=0,
                    success=True,
                )
                return cached

        result = fetch()
        try:
            write_cached_result(cache_file, result)
        except OSError:
            # Caching is an optimization. Keep the successful API result even
            # if the local cache cannot be written.
            pass
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 Index Hub API")
    parser.add_argument("--method", choices=("GET", "POST"), required=True)
    parser.add_argument("--path", required=True, help="接口相对路径，如 /skill/v2/index/detail")
    parser.add_argument("--query", help="GET 查询参数 JSON 对象")
    parser.add_argument("--body", help="POST 请求体 JSON 对象")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument(
        "--output",
        help="将完整 JSON 响应写入指定文件；同时仍保持 stdout 输出",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="忽略当前轮次缓存并重新请求；成功后更新缓存",
    )
    args = parser.parse_args()

    try:
        config = load_config()
        if not getattr(config, "API_KEY", ""):
            raise RuntimeError("API Key 未配置")
        query = parse_json_object(args.query, "query")
        body = parse_json_object(args.body, "body")
        result = request_with_turn_cache(
            config,
            args.method,
            args.path,
            query,
            body,
            args.timeout,
            args.refresh,
        )
        output_written = False
        if args.output:
            write_output_file(Path(args.output), result)
            output_written = True
        try:
            print(
                json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2)
            )
        except BrokenPipeError:
            # The consumer (e.g. jq) closed the pipe early. If the response was
            # also written to --output, the data is still available; otherwise
            # the caller will need to retry. Use os._exit to avoid Python's
            # interpreter shutdown from trying to flush the broken stdout.
            if output_written:
                os._exit(0)
            return 1
        return 0
    except (json.JSONDecodeError, ValueError, RuntimeError, urllib.error.URLError, OSError) as error:
        print(f"调用失败：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
