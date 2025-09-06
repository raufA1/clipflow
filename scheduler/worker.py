#!/usr/bin/env python3
import json, time, os, subprocess, datetime as dt
from scripts.logger import log
QUEUE="scheduler/queue.jsonl"
def parse_time(s): return dt.datetime.fromisoformat(s)
def main():
    while True:
        if not os.path.exists(QUEUE): time.sleep(5); continue
        lines=open(QUEUE,"r",encoding="utf-8").read().strip().splitlines(); new=[]
        now=dt.datetime.now().astimezone()
        for ln in lines:
            if not ln.strip(): continue
            try: job=json.loads(ln)
            except: continue
            t=job.get("publish_at"); when=parse_time(t) if t else now
            if now>=when:
                f=job["file"]; caption=job.get("caption",""); title=job.get("title", os.path.basename(f)); plats=job.get("platforms",["youtube"])
                for p in plats:
                    if p=="youtube":
                        subprocess.run(["python","publishers/youtube_upload.py","--file",f,"--title",title,"--desc",caption], check=False)
                    elif p=="instagram":
                        subprocess.run(["python","publishers/instagram_upload.py","--file",f,"--caption",caption], check=False)
                    elif p=="tiktok":
                        subprocess.run(["python","publishers/tiktok_upload.py","--file",f,"--caption",caption], check=False)
                log('queue_published', file=f, platforms=plats)
            else: new.append(ln)
        open(QUEUE,"w",encoding="utf-8").write("\n".join(new)); time.sleep(10)
if __name__=="__main__": main()
