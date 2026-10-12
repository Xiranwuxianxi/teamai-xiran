#!/usr/bin/env python3
"""
火灵 (huoling) 进度状态持久化脚本。
无第三方依赖。用于跨轮次/跨会话保持里程碑与进度一致。

用法:
  python progress_state.py init --task "实现 REST API" --milestones milestones.json
  python progress_state.py init --task "实现 REST API"  # 使用默认示例里程碑
  python progress_state.py update --id api-routes --status done --evidence "curl 200"
  python progress_state.py interrupt --mode suspend --new-task "修复登录样式" --reason "用户优先新需求"
  python progress_state.py interrupt --mode abort --new-task "重写前端" --reason "用户明确替换"
  python progress_state.py resume --task-id rest-api
  python progress_state.py show
  python progress_state.py bar  # 仅输出进度条行
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

STATE_FILE = Path(__file__).resolve().parent.parent / ".huoling-state.json"
BAR_WIDTH = 20


def default_milestones() -> list[dict]:
    return [
        {"id": "requirements", "name": "需求确认", "weight": 5, "status": "pending", "evidence": ""},
        {"id": "scaffold", "name": "项目脚手架", "weight": 10, "status": "pending", "evidence": ""},
        {"id": "data-model", "name": "数据模型", "weight": 15, "status": "pending", "evidence": ""},
        {"id": "api-routes", "name": "API 路由", "weight": 25, "status": "pending", "evidence": ""},
        {"id": "error-handling", "name": "错误处理", "weight": 10, "status": "pending", "evidence": ""},
        {"id": "unit-tests", "name": "单元测试", "weight": 20, "status": "pending", "evidence": ""},
        {"id": "e2e", "name": "端到端验证", "weight": 15, "status": "pending", "evidence": ""},
    ]


def load_state() -> dict:
    if not STATE_FILE.exists():
        print(f"状态文件不存在: {STATE_FILE}", file=sys.stderr)
        print("请先运行: python progress_state.py init --task \"你的任务\"", file=sys.stderr)
        sys.exit(1)
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def calc_progress(milestones: list[dict]) -> tuple[int, int]:
    active = [m for m in milestones if m["status"] != "cancelled"]
    total = sum(m["weight"] for m in active)
    if total == 0:
        return 0, 100
    done = sum(m["weight"] for m in active if m["status"] == "done")
    pct = round(done / total * 100)
    return pct, 100 - pct


def make_bar(pct: int) -> str:
    filled = round(pct / 5)
    filled = min(BAR_WIDTH, max(0, filled))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def count_done(milestones: list[dict]) -> tuple[int, int]:
    active = [m for m in milestones if m["status"] != "cancelled"]
    done = sum(1 for m in active if m["status"] == "done")
    return done, len(active)


def current_milestone(milestones: list[dict]) -> str:
    for m in milestones:
        if m["status"] == "doing":
            return m["name"]
    for m in milestones:
        if m["status"] == "pending":
            return m["name"]
    for m in milestones:
        if m["status"] == "suspended":
            return f"[挂起] {m['name']}"
    return "—"


def infer_phase(milestones: list[dict]) -> str:
    pending = [m for m in milestones if m["status"] in ("pending", "doing")]
    if not pending:
        return "收尾"
    name = pending[0]["name"].lower()
    if any(k in name for k in ("需求", "规划", "确认")):
        return "规划"
    if any(k in name for k in ("测试", "验证")):
        return "测试"
    if any(k in name for k in ("部署", "发布")):
        return "部署"
    return "实现"


def format_progress_block(state: dict) -> str:
    milestones = state["milestones"]
    pct, remaining = calc_progress(milestones)
    bar = make_bar(pct)
    done_n, total_n = count_done(milestones)
    current = current_milestone(milestones)
    phase = infer_phase(milestones)
    confidence = state.get("confidence", "中")
    eta = state.get("eta", "待估")

    lines = [
        "---",
        f"火灵 {bar} {pct}% | 剩余 {remaining}% | 阶段: {phase} | 置信度: {confidence}",
        f"当前: {current} | 已完成: {done_n}/{total_n} 里程碑 | ETA: {eta}",
        "---",
        "",
        "| 里程碑 | 权重 | 状态 | 验证证据 |",
        "|--------|------|------|----------|",
    ]
    for m in milestones:
        ev = m.get("evidence") or "—"
        if len(ev) > 60:
            ev = ev[:57] + "..."
        lines.append(f"| {m['name']} | {m['weight']}% | {m['status']} | {ev} |")
    return "\n".join(lines)


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.replace("█", "#").replace("░", "-"))


def cmd_init(args: argparse.Namespace) -> None:
    if args.milestones:
        with open(args.milestones, encoding="utf-8") as f:
            milestones = json.load(f)
    else:
        milestones = default_milestones()

    total_weight = sum(m["weight"] for m in milestones)
    if total_weight != 100:
        print(f"警告: 权重之和为 {total_weight}%，建议调整为 100%", file=sys.stderr)

    # 将第一项设为 doing
    has_doing = any(m["status"] == "doing" for m in milestones)
    if not has_doing:
        for m in milestones:
            if m["status"] == "pending":
                m["status"] = "doing"
                break

    state = {
        "task": args.task,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": args.confidence or "中",
        "eta": "待估",
        "milestones": milestones,
        "task_queue": [],
        "active_task": args.task,
    }
    save_state(state)
    safe_print(format_progress_block(state))
    safe_print(f"\n状态已保存: {STATE_FILE}")


def cmd_update(args: argparse.Namespace) -> None:
    state = load_state()
    found = False
    for m in state["milestones"]:
        if m["id"] == args.id:
            found = True
            m["status"] = args.status
            if args.evidence:
                m["evidence"] = args.evidence
            if args.status == "done":
                # 自动将下一项 pending 设为 doing
                idx = state["milestones"].index(m)
                for next_m in state["milestones"][idx + 1 :]:
                    if next_m["status"] == "pending":
                        next_m["status"] = "doing"
                        break
            break
    if not found:
        print(f"未找到里程碑 id: {args.id}", file=sys.stderr)
        sys.exit(1)
    if args.eta:
        state["eta"] = args.eta
    save_state(state)
    safe_print(format_progress_block(state))


def cmd_show(args: argparse.Namespace) -> None:
    state = load_state()
    safe_print(format_progress_block(state))
    # 也输出原始 JSON 供调试
    if args.verbose:
        print("\n--- JSON ---")
        print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_bar(args: argparse.Namespace) -> None:
    state = load_state()
    pct, remaining = calc_progress(state["milestones"])
    bar = make_bar(pct)
    safe_print(f"火灵 {bar} {pct}% | 剩余 {remaining}%")


def cmd_interrupt(args: argparse.Namespace) -> None:
    state = load_state()
    mode = args.mode.upper()
    old_task = state.get("active_task", state.get("task", ""))
    new_task = args.new_task
    reason = args.reason or ""

    if mode == "CONTINUE":
        state["task"] = f"{old_task}（含补充: {new_task}）"
        state["active_task"] = old_task
    elif mode == "ABORT":
        for m in state["milestones"]:
            if m["status"] in ("pending", "doing", "suspended"):
                m["status"] = "cancelled"
                m["evidence"] = f"ABORT: {reason}" if reason else "ABORT: 用户切换任务"
        state["task_queue"] = state.get("task_queue", [])
        state["task_queue"].append({"id": old_task, "status": "aborted", "task": old_task})
        state["task"] = new_task
        state["active_task"] = new_task
        state["milestones"] = default_milestones()
        for m in state["milestones"]:
            if m["status"] == "pending":
                m["status"] = "doing"
                break
    elif mode == "PARALLEL":
        queue = state.get("task_queue", [])
        queue.append({"id": new_task, "status": "active_parallel", "task": new_task})
        state["task_queue"] = queue
        state["task"] = f"{old_task} | 并行: {new_task}"
        # 里程碑由 agent 手动追加，不自动挂起原任务
    elif mode == "SUSPEND":
        for m in state["milestones"]:
            if m["status"] in ("pending", "doing"):
                m["status"] = "suspended"
        queue = state.get("task_queue", [])
        queue.append({"id": old_task, "status": "suspended", "task": old_task})
        state["task_queue"] = queue
        state["task"] = new_task
        state["active_task"] = new_task
        state["milestones"] = default_milestones()
        for m in state["milestones"]:
            if m["status"] == "pending":
                m["status"] = "doing"
                break
    elif mode == "MERGE":
        state["task"] = f"{old_task} + {new_task}"
        state["active_task"] = state["task"]
    else:
        print(f"未知模式: {mode}", file=sys.stderr)
        sys.exit(1)

    state["last_interrupt"] = {
        "mode": mode,
        "old_task": old_task,
        "new_task": new_task,
        "reason": reason,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(state)
    safe_print(f"> ⚡ 打断决策: {mode} | {reason}")
    safe_print(f"> 原任务: {old_task}")
    safe_print(f"> 新需求: {new_task}")
    safe_print("")
    safe_print(format_progress_block(state))


def cmd_resume(args: argparse.Namespace) -> None:
    state = load_state()
    # 挂起当前 doing，恢复第一个 suspended
    for m in state["milestones"]:
        if m["status"] == "doing":
            m["status"] = "suspended"
    resumed = False
    for m in state["milestones"]:
        if m["status"] == "suspended":
            m["status"] = "doing"
            resumed = True
            break
    if not resumed:
        for m in state["milestones"]:
            if m["status"] == "pending":
                m["status"] = "doing"
                break
    if args.task_id:
        state["active_task"] = args.task_id
        state["task"] = args.task_id
    save_state(state)
    safe_print(f"> 恢复: {state.get('active_task', state.get('task', ''))}")
    safe_print(format_progress_block(state))


def main() -> None:
    parser = argparse.ArgumentParser(description="火灵进度状态管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="初始化任务与里程碑")
    p_init.add_argument("--task", required=True, help="任务描述")
    p_init.add_argument("--milestones", help="里程碑 JSON 文件路径")
    p_init.add_argument("--confidence", choices=["高", "中", "低"], default="中")
    p_init.set_defaults(func=cmd_init)

    p_up = sub.add_parser("update", help="更新里程碑状态")
    p_up.add_argument("--id", required=True, help="里程碑 id")
    p_up.add_argument("--status", required=True, choices=["pending", "doing", "done", "failed", "blocked", "suspended", "cancelled"])
    p_up.add_argument("--evidence", default="", help="验证证据")
    p_up.add_argument("--eta", help="更新 ETA")
    p_up.set_defaults(func=cmd_update)

    p_show = sub.add_parser("show", help="显示当前进度")
    p_show.add_argument("-v", "--verbose", action="store_true")
    p_show.set_defaults(func=cmd_show)

    p_bar = sub.add_parser("bar", help="仅输出进度条一行")
    p_bar.set_defaults(func=cmd_bar)

    p_int = sub.add_parser("interrupt", help="处理用户打断与新需求")
    p_int.add_argument("--mode", required=True, choices=["continue", "parallel", "suspend", "merge", "abort"])
    p_int.add_argument("--new-task", required=True, help="新需求描述")
    p_int.add_argument("--reason", default="", help="判定理由")
    p_int.set_defaults(func=cmd_interrupt)

    p_res = sub.add_parser("resume", help="恢复挂起的原任务")
    p_res.add_argument("--task-id", default="", help="要恢复的任务 id")
    p_res.set_defaults(func=cmd_resume)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
