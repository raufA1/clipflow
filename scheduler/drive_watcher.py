#!/usr/bin/env python3
import time, os, subprocess, pathlib
from scripts.logger import log
INBOX="inbox"
def main():
    os.makedirs(INBOX, exist_ok=True); print("Watching inbox/ ..."); seen=set(os.listdir(INBOX))
    while True:
        cur=set(os.listdir(INBOX)); new=[f for f in (cur-seen) if f.lower().endswith((".mp4",".mov",".mkv"))]
        for f in new:
            path=os.path.join(INBOX,f)
            subprocess.run(["python","analyzer/analyze.py", path], check=False)
            meta = os.path.join(".work", pathlib.Path(path).stem+".json")
            subprocess.run(["python","nlp/caption_ai.py", meta, os.path.join(".work", pathlib.Path(path).stem+"_captions_A.json"), "A"], check=False)
            subprocess.run(["python","nlp/caption_ai.py", meta, os.path.join(".work", pathlib.Path(path).stem+"_captions_B.json"), "B"], check=False)
            subprocess.run(["python","processor/highlight.py", meta, os.path.join(".work", pathlib.Path(path).stem+"_highlights.json")], check=False)
            subprocess.run(["python","processor/render.py", meta], check=False)
            log('inbox_processed', file=path)
        seen=cur; time.sleep(3)
if __name__=="__main__": main()
