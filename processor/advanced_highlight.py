#!/usr/bin/env python3
import json, sys, cv2, numpy as np, os, yaml

def attention_center(video_path, start, end):
    cap=cv2.VideoCapture(video_path)
    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(start*fps))
    heat=None; count=0
    ok, prev = cap.read()
    if not ok: return None
    while True:
        t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
        if t>end: break
        ok, cur = cap.read()
        if not ok: break
        diff = cv2.absdiff(cur, prev)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray,(9,9),0)
        if heat is None: heat = blur.astype(np.float32)
        else: heat = heat*0.95 + blur*0.05
        prev=cur; count+=1
    cap.release()
    if heat is None: return None
    y,x=np.unravel_index(np.argmax(heat), heat.shape)
    return int(x), int(y), heat.shape[1], heat.shape[0]

def main(meta_json, segs_json, out_json):
    meta=json.load(open(meta_json,"r",encoding="utf-8"))
    segs=json.load(open(segs_json,"r",encoding="utf-8"))
    video = os.path.join("inbox", meta["video"])
    if not os.path.exists(video): video = meta["video"]
    out=[]
    for s in segs:
        cxcy = attention_center(video, s["start"], s["end"])
        if cxcy:
            cx,cy,w,h = cxcy
            out.append({**s, "pan_x": float(max(0, cx-540)), "pan_y": float(max(0, cy-960))})
        else:
            out.append({**s, "pan_x": None, "pan_y": None})
    json.dump(out, open(out_json,"w",encoding="utf-8"), ensure_ascii=False, indent=2); print(out_json)

if __name__=="__main__":
    if len(sys.argv)<4: print("Usage: python processor/advanced_highlight.py .work/meta.json .work/segs.json .work/segs_pan.json"); raise SystemExit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
