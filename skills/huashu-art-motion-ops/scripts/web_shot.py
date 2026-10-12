"""网页整屏截图（防碎图版）——替代裸 chrome --screenshot。

用法：
  python3 web_shot.py <url> <输出.png> [--wait 3] [--scale 2] [--tall 3000] [--hide ".banner" ".cookie"]

防碎图三件套（2026-10-10 碎图事故后定型）：
  1. networkidle 等网络静默 + 额外 wait 秒
  2. LAZY 滚动触发懒加载图片（滚到底再回顶）
  3. 截完自检：行方差<5 的空白行占比 >30%（浅色页）判碎图，退出码 2
深色主题页（如 nvidia）空白行天然高，用 --dark 跳过碎图判定。
"""
import argparse, sys
import numpy as np
from PIL import Image
from playwright.sync_api import TimeoutError as PwTimeout, sync_playwright

LAZY = """async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const els = [document.scrollingElement, ...document.querySelectorAll('*')].filter(e => e && (e === document.scrollingElement ||
    (e.scrollHeight > e.clientHeight + 200 && /(auto|scroll)/.test(getComputedStyle(e).overflowY || ''))));
  for (const s of els.slice(0, 8)) {
    for (let y = 0; y < Math.min(s.scrollHeight, 20000); y += 700) { s.scrollTop = y; await sleep(80); }
    s.scrollTop = 0;
  }
  window.scrollTo(0, 0);
}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url'); ap.add_argument('out')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--scale', type=float, default=2)
    ap.add_argument('--tall', type=int)
    ap.add_argument('--wait', type=float, default=2.5)
    ap.add_argument('--hide', nargs='*', default=[])
    ap.add_argument('--dark', action='store_true')
    a = ap.parse_args()

    with sync_playwright() as p:
        ctx = p.chromium.launch().new_context(
            viewport={'width': a.width, 'height': a.tall or a.height},
            device_scale_factor=a.scale)
        pg = ctx.new_page()
        pg.goto(a.url, wait_until='load', timeout=90000)
        try: pg.wait_for_load_state('networkidle', timeout=15000)
        except PwTimeout: pass
        pg.wait_for_timeout(int(a.wait * 1000))
        pg.evaluate(LAZY); pg.wait_for_timeout(800)
        for sel in a.hide:
            pg.add_style_tag(content=f'{sel} {{ display: none !important; }}')
        pg.screenshot(path=a.out)
        ctx.close()

    im = np.array(Image.open(a.out).convert('L'), dtype=float)
    blank = (im.var(axis=1) < 5).mean() * 100
    print(f'{a.out} {im.shape[1]}x{im.shape[0]} 空白行{blank:.1f}% var{im.var():.0f}')
    if not a.dark and blank > 30:
        print('⚠️ 疑似碎图（半加载），换 --wait 更久重截'); sys.exit(2)
    print('OK')

if __name__ == '__main__':
    main()
