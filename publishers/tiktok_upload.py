#!/usr/bin/env python3
import os, sys, argparse, requests
from scripts.logger import log

API=os.environ.get("TT_API_BASE","https://open-api.tiktok.com")

def _retry(fn, tries=5, base=1.5):
    import time, random
    for i in range(tries):
        try: return fn()
        except Exception as e:
            if i==tries-1: raise
            time.sleep(base*(2**i)+random.random())

def auth_headers():
    tok=os.environ.get("TT_ACCESS_TOKEN")
    if not tok: print("Missing TT_ACCESS_TOKEN"); sys.exit(2)
    return {"Authorization": f"Bearer {tok}"}

def init_upload():
    r=requests.post(f"{API}/video/upload/initialize/", headers=auth_headers(), json={})
    if r.status_code>=300: print("Init failed:", r.text); sys.exit(1)
    d=r.json(); return d.get("data",{}).get("upload_url"), d.get("data",{}).get("upload_id")

def publish(upload_id, text):
    r=requests.post(f"{API}/video/publish/", headers=auth_headers(), json={"upload_id":upload_id,"text":text})
    if r.status_code>=300: print("Publish failed:", r.text); sys.exit(1)
    log('publish_done', platform='tiktok'); print("TikTok published:", r.json())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--file",required=True); ap.add_argument("--caption",default=""); a=ap.parse_args()
    up_url, up_id = init_upload()
    with open(a.file,"rb") as f:
        r=requests.put(up_url, data=f.read())
    if r.status_code not in (200,201): print("Upload failed:", r.text); sys.exit(1)
    publish(up_id, a.caption)

if __name__=="__main__": main()
