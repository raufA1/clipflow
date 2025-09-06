#!/usr/bin/env python3
import csv, os, sys, json


"""
Simple content-safety guard for music:
- Reads assets/music/metadata.csv (file,bpm,energy,license,source_url)
- Fails if selected background track has license not in {'royalty_free','cleared'}
- Warns if metadata missing.

Integrate this before publish to reduce copyright risk.
"""

META="assets/music/metadata.csv"

def check_track(path):
    if not os.path.exists(META):
        print("WARN: metadata.csv missing; skipping"); return True
    rows={}
    import csv
    with open(META,"r",encoding="utf-8") as f:
        rdr=csv.DictReader(f)
        for r in rdr: rows[r["file"]]=r
    name=os.path.basename(path)
    if name not in rows:
        print(f"WARN: {name} not present in metadata.csv"); return True
    lic=rows[name].get("license","").lower()
    if lic not in {"royalty_free","cleared"}:
        print(f"FAIL: {name} license='{lic}' not allowed")
        return False
    return True

def main(file_under_out):
    # naive: find a matching music source in logs (optional) or trust metadata only
    # Here we only check metadata presence for all files in assets/music/
    ok=True
    for f in os.listdir("assets/music"):
        if f.lower().endswith((".mp3",".wav",".m4a",".flac",".ogg")):
            ok = check_track(os.path.join("assets/music",f)) and ok
    if not ok:
        sys.exit(3)
    print("Content-safety OK")

if __name__=="__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv)>=2 else ""
    main(arg)
