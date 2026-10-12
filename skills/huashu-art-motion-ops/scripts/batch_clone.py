#!/usr/bin/env python3
"""批量克隆配音（断点续跑 + 三级故障切换）。

用法：
  python3 batch_clone.py --work /root/<proj>-work --script script.json
  python3 batch_clone.py --work . --script script.json --only 1 3   # 只补某几段

工程目录放 script.json：
  {"segs": [{"id": 1, "tts": "喂稿（数字写中文、易飘英文谐音锚定）"}, ...]}
输出：<work>/seg<id>.wav（已存在且 >20KB 自动跳过，断点续跑）

每段按顺序尝试：F5-TTS 带 token → F5-TTS 匿名（两套独立 ZeroGPU 配额）→
CosyVoice2-0.5B。段间失败 sleep 50s。任何一段三通道全灭才 exit 1。

前置：/root/.hf_token 存在；声纹参考 /root/voice-assets/ref_clip.wav 在。
REF_TEXT 必须与参考音频逐字一致（当前值来自 /root/voice-assets/clone2.py，换参考音必须换它）。
"""
import argparse, json, os, sys, time, urllib.request

DEFAULT_REF_TEXT = "百分之八十七点五的用户表示满意，这个数字还在增长。说实话，技术本身没有对错，关键是看你怎么用它。"
F5_SPACE = "https://mrfakename-e2-f5-tts.hf.space"
COSY_SPACE = "https://taoyy-cosyvoice2-0-5b.hf.space"


def post(url, data, headers, timeout=180):
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout)


class Cloner:
    def __init__(self, ref_path, ref_text, token_path="/root/.hf_token"):
        self.ref_path, self.ref_text = ref_path, ref_text
        self.token = open(token_path).read().strip()
        self._uploaded = {}  # space base -> server path（同一 space 只上传一次）

    def upload(self, base, hdr):
        if base in self._uploaded:
            return self._uploaded[base]
        boundary = "----vcform"
        audio = open(self.ref_path, "rb").read()
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"ref.wav\"\r\n"
                f"Content-Type: audio/wav\r\n\r\n").encode() + audio + f"\r\n--{boundary}--\r\n".encode()
        h = dict(hdr); h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        self._uploaded[base] = json.loads(post(base + "/gradio_api/upload", body, h).read())[0]
        return self._uploaded[base]

    def _call(self, base, endpoint, payload, out, hdr):
        h = dict(hdr); h["Content-Type"] = "application/json"
        eid = json.loads(post(base + endpoint, json.dumps(payload).encode(), h).read())["event_id"]
        for _ in range(120):
            time.sleep(3)
            txt = urllib.request.urlopen(urllib.request.Request(f"{base}{endpoint}/{eid}", headers=hdr), timeout=60).read().decode()
            if "event: error" in txt:
                return None
            if "event: complete" in txt:
                url = json.loads([l for l in txt.splitlines() if l.startswith("data: ")][-1][6:])[0]["url"]
                url = url.replace("/grad/gradio_api/file=", "/gradio_api/file=")  # CosyVoice 的坑：不改下到 HTML 错误页
                with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=120) as r, open(out, "wb") as f:
                    f.write(r.read())
                return out
        return None

    def f5(self, gen_text, out, use_token=True):
        hdr = {"Authorization": f"Bearer {self.token}"} if use_token else {}
        sp = self.upload(F5_SPACE, hdr)
        payload = {"data": [{"path": sp, "meta": {"_type": "gradio.FileData"}, "orig_name": "ref.wav"},
                             self.ref_text, gen_text, False]}
        return self._call(F5_SPACE, "/gradio_api/call/predict", payload, out, hdr)

    def cosy(self, gen_text, out):
        hdr = {"Authorization": f"Bearer {self.token}"}
        sp = self.upload(COSY_SPACE, hdr)
        payload = {"data": [gen_text, "零样本语音复刻",
                             {"path": sp, "meta": {"_type": "gradio.FileData"}, "orig_name": "ref.wav"},
                             self.ref_text, None, 1.0]}
        return self._call(COSY_SPACE, "/gradio_api/call/synthesize", payload, out, hdr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=".")
    ap.add_argument("--script", default="script.json")
    ap.add_argument("--ref", default="/root/voice-assets/ref_clip.wav")
    ap.add_argument("--ref-text", default=DEFAULT_REF_TEXT)
    ap.add_argument("--only", type=int, nargs="*", default=None, help="只跑这些段号（补跑用）")
    a = ap.parse_args()

    segs = json.load(open(os.path.join(a.work, a.script)))["segs"]
    cloner = Cloner(a.ref, a.ref_text)

    for s in segs:
        sid, out = s["id"], os.path.join(a.work, f"seg{s['id']}.wav")
        if a.only and sid not in a.only:
            continue
        if os.path.exists(out) and os.path.getsize(out) > 20000:
            print(f"seg{sid} skip (已存在)"); continue
        ok = None
        for name, fn in (("f5-token", lambda: cloner.f5(s["tts"], out, True)),
                         ("f5-anon", lambda: cloner.f5(s["tts"], out, False)),
                         ("cosy", lambda: cloner.cosy(s["tts"], out))):
            try:
                ok = fn()
            except Exception as e:
                print(f"seg{sid} {name} 异常: {e}")
            if ok:
                print(f"seg{sid} OK via {name}"); break
            time.sleep(50)
        if not ok:
            print(f"seg{sid} 三通道全灭"); sys.exit(1)
    print("ALL_VOICE_DONE")


if __name__ == "__main__":
    main()
