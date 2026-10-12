# Rigor experiment patterns (reviewer-proofing)

Reusable code patterns for responding to methodology reviewers. Origin: sentiment-classification paper revision on a 2 vCPU / 2 GB server (nlp-paper-sentiment).

## Resource logging (answers "no resource evidence")

```python
import resource, threading, time, os
swap_peak = {"used_mb": 0.0}; stop = {"x": False}
def swap_used_mb():
    d = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo") if ":" in l}
    return (d.get("SwapTotal", 0) - d.get("SwapFree", 0)) / 1024.0
def sampler():
    while not stop["x"]:
        swap_peak["used_mb"] = max(swap_peak["used_mb"], swap_used_mb()); time.sleep(2)
threading.Thread(target=sampler, daemon=True).start()
peak_rss_mb = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
load1 = lambda: os.getloadavg()[0]
# snapshot all three at each phase boundary; one OOM ≠ proof, so report peaks instead
```

## Single-request latency (answers "batch average ≠ latency")

```python
def latency_single(fn, n=50, warmup=5):
    for _ in range(warmup): fn()
    ts = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); ts.append((time.perf_counter()-t0)*1000)
    return {"median_ms": float(np.median(ts)), "p95_ms": float(np.percentile(ts, 95))}
# TF-IDF arm: vectorize one doc + predict. Transformer arm: tokenize+forward one doc.
```

Also split the clock: feature_build_time / clf_fit_time / total_encode_time / e2e single-request — never call classifier fit "training" when feature construction dominates.

## Paired statistics (answers "no significance")

```python
def bootstrap_ci_diff(y, pa, pb, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    ca = (np.asarray(pa) == y).astype(float); cb = (np.asarray(pb) == y).astype(float)
    d = [(ca[rng.integers(0,len(y),len(y))].mean() - cb[rng.integers(0,len(y),len(y))].mean()) for _ in range(n)]
    return np.percentile(d, [2.5, 97.5])

def mcnemar(y, pa, pb):
    from math import comb
    a_ok = np.asarray(pa) == y; b_ok = np.asarray(pb) == y
    b, c = int((a_ok & ~b_ok).sum()), int((~a_ok & b_ok).sum()); n = b + c
    p = 1.0 if n == 0 else min(1.0, 2*sum(comb(n,i) for i in range(min(b,c)+1))/2**n)
    return {"b": b, "c": c, "p": p}
```

Save per-sample predictions every seed: `np.savez_compressed(f"preds_{lang}_s{seed}.npz", y=..., svm=..., cls=...)` — enables any post-hoc paired test.

## Cheap multi-seed via embedding cache

Encode the full corpus once per model, save `.npz` (cls + mean pooling from the SAME forward pass — pooling ablation is free), then multi-seed = re-split indices + retrain linear heads. Subsample seeds (where the text SET changes) still cost one encode each; decide the count from measured per-encode time.

## Fairness controls

- Truncation: report fraction of samples exceeding max_len + p50/p95 lengths (sample 2000 for speed).
- Matched-input arm: truncate texts with the same tokenizer (`tok.convert_tokens_to_string(tok.tokenize(t)[:max_len-2])`) and re-run the cheap baseline on them.
- Data integrity: exact-duplicate count, train/test exact-text overlap per split, class ratios, dataset source + snapshot date.

## Ops

- Long runs: `terminal(background=true, notify=true)` + `tee log`. Piped stdout is block-buffered: empty log for minutes is normal, verify with `ps`, not by rerunning.
- `nohup ... &` is rejected by the Hermes terminal tool — use background=true instead.
