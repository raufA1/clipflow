#!/usr/bin/env python3
import json, yaml, sys, os

def load_config():
    import pathlib, yaml
    return yaml.safe_load(open(str(pathlib.Path(__file__).resolve().parents[1]/"config/config.yaml"),"r",encoding="utf-8"))

def windows(duration, w):
    t=0.0
    while t+w<=duration:
        yield (t, t+w); t += w/4.0

def pick_top(meta, lengths):
    ev = meta["events"]; dur = meta["duration"]
    picks=[]; taken=[]
    def overlaps(a,b): return not (a[1]<=b[0] or b[1]<=a[0])
    for L in lengths:
        best=(0.0,(0.0,L))
        for win in windows(dur, L):
            score = sum(1 for e in ev if win[0]<=e["t"]<=win[1])
            if score>best[0]: best=(score, win)
        win=best[1]
        if any(overlaps(win,x) for x in taken):
            shifted=(max(0.0,win[0]-L/2), max(L, min(dur, win[1]-L/2)))
            win=shifted
        picks.append({"file":meta['video'],"start":round(win[0],2),"end":round(win[1],2)})
        taken.append(win)
    return picks

def main(meta_json, out_json):
    cfg=load_config(); meta=json.load(open(meta_json,"r",encoding="utf-8"))
    dur=meta.get("duration",0.0)
    if not cfg.get("enable_highlights",True) or dur<=float(cfg.get("highlight_threshold_sec",90)):
        open(out_json,"w",encoding="utf-8").write("[]"); print(out_json); return
    targets=cfg.get("highlight_targets_sec",[15,30,60])
    out=pick_top(meta, targets)
    json.dump(out, open(out_json,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__=="__main__":
    if len(sys.argv)<3: print("Usage: python processor/highlight.py .work/video.json .work/highlights.json"); raise SystemExit(2)
    main(sys.argv[1], sys.argv[2])
