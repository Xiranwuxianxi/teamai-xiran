# -*- coding: utf-8 -*-
"""财经电报/快讯数据获取（依赖 neodata-financial-search）

通过 neodata 自然语言查询获取财经快讯/电报内容。
用法：python fetch_cls_telegraph.py [--neodata-scripts <neodata skill 的 scripts 路径>]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def run_neodata_query(query_text: str, scripts_path: str) -> dict:
    """向 neodata 发起查询"""
    query_bin = str(Path(scripts_path) / "query.py")
    proc_result = subprocess.run(
        [sys.executable, query_bin, "--query", query_text],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc_result.returncode != 0:
        print(f"查询失败: {proc_result.stderr.strip()}", file=sys.stderr)
        return {}
    try:
        return json.loads(proc_result.stdout)
    except json.JSONDecodeError:
        print(f"响应解析失败: {proc_result.stdout[:200]}", file=sys.stderr)
        return {}


def collect_articles(raw_data: dict) -> list:
    """从 neodata 响应中提取文章列表"""
    items = []
    doc_data = raw_data.get("data", {}).get("docData", {})
    doc_recall = doc_data.get("docRecall", [])
    for batch in doc_recall:
        for entry in batch.get("docList", []):
            items.append({
                "title": entry.get("title", ""),
                "content": entry.get("content", ""),
                "publishTime": entry.get("publishTime", 0),
                "source": entry.get("source", ""),
                "url": entry.get("url", ""),
            })
    return items


def format_item(article: dict) -> dict:
    """将单条记录归一化为展示格式"""
    title_text = article.get("title", "")
    body_text = article.get("content", "")
    unix_ts = article.get("publishTime", 0)

    # 标题不在正文中时拼接为前缀
    if title_text and title_text not in body_text:
        display_text = f"{title_text}｜{body_text}"
    else:
        display_text = body_text

    # Unix 时间戳 → 本地 HH:MM
    formatted_time = time.strftime("%H:%M", time.localtime(unix_ts)) if unix_ts else ""

    return {
        "display": display_text,
        "time_str": formatted_time,
        "source": article.get("source", ""),
        "url": article.get("url", ""),
    }


def collect_telegraph(scripts_path: str):
    """拉取最新财经快讯/电报"""
    query_list = [
        "今日财经快讯 财联社电报",
        "A股市场最新快讯",
        "港股市场最新快讯",
    ]

    collected = []
    visited_urls = set()

    for q in query_list:
        print(f"查询: {q}", file=sys.stderr)
        raw = run_neodata_query(q, scripts_path)
        if not raw:
            continue

        articles = collect_articles(raw)
        print(f"  获取 {len(articles)} 条", file=sys.stderr)

        for art in articles:
            link = art.get("url", "")
            if link and link in visited_urls:
                continue
            if link:
                visited_urls.add(link)
            collected.append(art)

    # 按时间倒序
    collected.sort(key=lambda x: x.get("publishTime", 0), reverse=True)

    print(f"\n共获取 {len(collected)} 条（去重后）\n")

    for art in collected[:20]:  # 默认展示前 20 条
        fmt = format_item(art)
        print(f"[{fmt['source']}] {fmt['time_str']} | {fmt['display'][:100]}")
        if fmt["url"]:
            print(f"  链接: {fmt['url']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="财经快讯/电报获取（基于 neodata-financial-search）")
    parser.add_argument(
        "--neodata-scripts",
        default=None,
        help="neodata-financial-search skill 的 scripts 目录路径",
    )
    args = parser.parse_args()

    # 自动探测 neodata 脚本路径
    if args.neodata_scripts:
        scripts_path = args.neodata_scripts
    else:
        # 尝试常见安装位置
        possible_dirs = [
            Path.home() / ".workbuddy" / "skills" / "neodata-financial-search" / "scripts",
            Path.home() / ".openclaw" / "skills" / "neodata-financial-search" / "scripts",
        ]
        scripts_path = None
        for candidate in possible_dirs:
            if (candidate / "query.py").exists():
                scripts_path = str(candidate)
                break
        if not scripts_path:
            print("错误: 未找到 neodata-financial-search 的 scripts 目录", file=sys.stderr)
            print("请通过 --neodata-scripts 参数指定路径", file=sys.stderr)
            sys.exit(1)

    collect_telegraph(scripts_path)


if __name__ == "__main__":
    main()
