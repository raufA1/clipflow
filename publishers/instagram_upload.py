#!/usr/bin/env python3
import os, sys, argparse, time, requests
from scripts.logger import log

def _retry(fn, tries=5, base=1.5):
    import time, random
    for i in range(tries):
        try: return fn()
        except Exception as e:
            if i==tries-1: raise
            time.sleep(base*(2**i)+random.random())

def graph_base():
    ver=os.environ.get("IG_API_VERSION","v20.0"); return f"https://graph.facebook.com/{ver}"

def post_retry(url, data=None, files=None, max_try=3, timeout=300):
    for i in range(1,max_try+1):
        r=requests.post(url, data=data, files=files, timeout=timeout)
        if r.status_code<300: return r
        if i==max_try: return r
        time.sleep(2*i)

def upload_file(path, caption, token, user_id):
    url=f"{graph_base()}/{user_id}/media"; files={"video_file": open(path,"rb")}
    data={"caption":caption,"media_type":"REELS","access_token":token}; return post_retry(url, data=data, files=files)

def upload_url(vurl, caption, token, user_id):
    url=f"{graph_base()}/{user_id}/media"; data={"caption":caption,"media_type":"REELS","video_url":vurl,"access_token":token}
    return post_retry(url, data=data, files=None)

def publish(cid, token, user_id):
    url=f"{graph_base()}/{user_id}/media_publish"; return post_retry(url, data={"creation_id":cid,"access_token":token}, files=None, timeout=120)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--file"); ap.add_argument("--video-url"); ap.add_argument("--caption",default=""); a=ap.parse_args()
    tok=os.environ.get("IG_ACCESS_TOKEN"); uid=os.environ.get("IG_USER_ID")
    if not tok or not uid: print("Missing IG_ACCESS_TOKEN or IG_USER_ID"); sys.exit(2)
    if not a.file and not a.video_url: print("Provide --file or --video-url"); sys.exit(2)
    r=upload_url(a.video_url,a.caption,tok,uid) if a.video_url else upload_file(a.file,a.caption,tok,uid)
    if r.status_code>=300: print("Container failed:", r.text); sys.exit(1)
    cid=r.json().get("id"); print("Container:", cid)
    pub=publish(cid,tok,uid)
    if pub.status_code>=300: print("Publish failed:", pub.text); sys.exit(1)
    log('publish_done', platform='instagram'); print("Published:", pub.json())

if __name__=="__main__": main()
