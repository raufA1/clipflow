import os, sys, json, random, subprocess, yaml
from scripts.logger import log

ASS_HEADER = r'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,64,&H00FFFFFF,&H000000FF,&H80000000,&H50000000,0,0,0,0,100,100,0,0,1,4,0,2,60,60,120,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def load_config():
    import pathlib, yaml
    return yaml.safe_load(open(str(pathlib.Path(__file__).resolve().parents[1]/"config/config.yaml"),"r",encoding="utf-8"))

def load_captions_yaml(path="processor/captions.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ts(t):
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f"{h:d}:{m:02d}:{int(s):02d}.{int((s-int(s))*100):02d}"

def pick_music(music_dir="assets/music"):
    if not os.path.isdir(music_dir): return None
    tracks=[os.path.join(music_dir,f) for f in os.listdir(music_dir) if f.lower().endswith((".mp3",".wav",".m4a",".flac"))]
    return random.choice(tracks) if tracks else None

def pick_music_vibe(meta, music_dir="assets/music"):
    import csv
    meta_csv = os.path.join(music_dir, "metadata.csv")
    if not os.path.exists(meta_csv):
        return pick_music(music_dir)
    dur = max(meta.get("duration", 0.0), 1.0)
    evpm = 60.0 * max(1, len(meta.get("events", []))) / dur
    target_bpm = 140 if evpm > 3 else (115 if evpm > 1.5 else 95)
    target_energy = 0.8 if evpm > 3 else (0.6 if evpm > 1.5 else 0.4)
    tracks=[]
    with open(meta_csv, "r", encoding="utf-8") as f:
        import csv
        rdr = csv.DictReader(f)
        for row in rdr:
            row_bpm = float(row.get("bpm", 110)); row_en = float(row.get("energy", 0.6))
            score = abs(row_bpm-target_bpm)+abs(row_en-target_energy)
            tracks.append((row["file"], score))
    tracks.sort(key=lambda x: x[1])
    for name,_ in tracks:
        p = os.path.join(music_dir, name)
        if os.path.exists(p): return p
    return pick_music(music_dir)

def main(meta_path, start=None, end=None, pan_x=None, pan_y=None):
    cfg = load_config()
    meta = json.load(open(meta_path, "r", encoding="utf-8"))
    caps = load_captions_yaml()
    rules = caps.get("rules",{}); langs = caps.get("languages",{})
    lang_order = [cfg.get("language","az")] + [x for x in rules.get("lang_priority",["az","en","ru"]) if x!=cfg.get("language","az")]
    prob = float(rules.get("prob_per_event", 0.7))
    max_per_min = int(rules.get("max_per_minute", 6))

    base = meta["video"].rsplit(".",1)[0]
    raw = os.path.join("inbox", meta["video"])
    if not os.path.isfile(raw): raw = meta["video"]

    ass_lines=[ASS_HEADER]; placed=[]
    def can_place(t):
        win=[x for x in placed if abs(x-t)<60]; return len(win)<max_per_min
    def tpl(tp):
        for lg in lang_order:
            if lg in langs and tp in langs[lg]: return random.choice(langs[lg][tp])
        return tp.upper()

    events = meta["events"]
    if start is not None and end is not None:
        events = [e for e in events if start <= e["t"] <= end]

    for e in events:
        import random
        if random.random()>prob: continue
        if not can_place(e["t"]): continue
        ass_lines.append(f"Dialogue: 0,{ts(max(0,(e['t']-(start or 0))-0.1))},{ts((e['t']-(start or 0))+1.9)},Cap,,0,0,0,,{tpl(e['type'])}")
        placed.append(e["t"])

    ass_path = os.path.join(".work", base+("_seg" if start is not None else "")+".ass")
    open(ass_path,"w",encoding="utf-8").write("".join(ass_lines))

    logo = "assets/logo.png"
    music = pick_music_vibe(meta)

    crop = f"crop=1080:1920" if (pan_x is None or pan_y is None) else f"crop=1080:1920:x={int(pan_x)}:y={int(pan_y)}"
    extra = ",zoompan=z='min(zoom+0.0015,1.1)':d=60:s=1080x1920" if (start is not None and end is not None) else ""
    vf = f"scale=-2:1920:flags=lanczos,{crop},format=yuv420p{extra},subtitles='{ass_path}'"

    ss_args=[]
    if start is not None and end is not None:
        ss_args=["-ss", str(start), "-to", str(end)]

    cmd = ["ffmpeg","-y"]+ss_args+["-i",raw]
    if os.path.exists(logo):
        cmd += ["-i",logo,"-filter_complex", f"[0:v]{vf}[v0];[v0][1:v]overlay=60:60:format=auto[v]","-map","[v]"]
    else:
        cmd += ["-vf", vf]

    if music:
        cmd += ["-i", music, "-filter_complex",
                f"[0:a]alimiter=limit=0.98[a0];[2:a]volume={cfg.get('music',{}).get('fallback_gain',0.25)},atrim=0,setpts=PTS-STARTPTS[a1];"
                f"[a0][a1]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=200:makeup=6,aloudnorm=I=-16:TP=-1.5:LRA=11[aout]",
                "-map","[aout]"]
    else:
        cmd += ["-c:a","aac"]

    out_dir="out"; os.makedirs(out_dir, exist_ok=True)
    suffix = "_HIGHLIGHT" if start is not None else ""
    out_path = os.path.join(out_dir, base+f"{suffix}_VERT.mp4")
    cmd += ["-c:v","libx264","-preset","veryfast","-crf","20","-r","30", out_path]
    subprocess.run(cmd, check=False)
    log('render_done', out=out_path, segment=bool(start is not None))
    print(out_path)

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python processor/render.py .work/<video>.json [start end pan_x pan_y]"); raise SystemExit(2)
    if len(sys.argv)>=6:
        main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
    elif len(sys.argv)==4:
        main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    else:
        main(sys.argv[1])
