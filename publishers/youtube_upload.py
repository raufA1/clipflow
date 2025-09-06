#!/usr/bin/env python3
import os, sys, argparse, datetime as dt
from scripts.logger import log
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES=["https://www.googleapis.com/auth/youtube.upload"]
ROOT=os.path.dirname(os.path.dirname(__file__))
CLIENT_SECRET=os.path.join(ROOT,"client_secret.json")
TOKEN_FILE=os.path.join(ROOT,"yt_token.json")

def _retry(fn, tries=5, base=1.5):
    import time, random
    for i in range(tries):
        try: return fn()
        except Exception as e:
            if i==tries-1: raise
            time.sleep(base*(2**i)+random.random())

def creds():
    cid=os.environ.get("YT_CLIENT_ID"); cs=os.environ.get("YT_CLIENT_SECRET"); rt=os.environ.get("YT_REFRESH_TOKEN")
    if cid and cs and rt:
        c=Credentials(None, refresh_token=rt, token_uri="https://oauth2.googleapis.com/token", client_id=cid, client_secret=cs, scopes=SCOPES)
        c.refresh(Request()); return c
    if os.path.exists(TOKEN_FILE):
        c=Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if c and c.valid: return c
        if c and c.expired and c.refresh_token: c.refresh(Request()); return c
    if not os.path.exists(CLIENT_SECRET): raise SystemExit("Missing client_secret.json or CI envs")
    flow=InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES); c=flow.run_local_server(port=0)
    open(TOKEN_FILE,"w").write(c.to_json()); return c

def upload(path,title,desc,tags,publish_at):
    c=creds(); svc=build("youtube","v3",credentials=c)
    body={"snippet":{"title":title,"description":desc,"tags":tags,"categoryId":"20"},"status":{"privacyStatus":"private"}}
    if publish_at:
        when=dt.datetime.fromisoformat(publish_at).astimezone(dt.timezone.utc).isoformat()
        body["status"]["publishAt"]=when
    from googleapiclient.http import MediaFileUpload
    media=MediaFileUpload(path, chunksize=-1, resumable=True)
    req=svc.videos().insert(part="snippet,status", body=body, media_body=media); resp=None
    while resp is None:
        status, resp = req.next_chunk()
        if status: print(f"Upload {int(status.progress()*100)}%")
    vid=resp["id"]; log('publish_uploaded', platform='youtube', video_id=vid); print("Video ID:", vid)
    if not publish_at:
        svc.videos().update(part="status", body={"id":vid,"status":{"privacyStatus":"public"}}).execute()
        print("Published now.")
    else:
        print("Scheduled publish at:", publish_at)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--file",required=True); ap.add_argument("--title",required=True)
    ap.add_argument("--desc",default=""); ap.add_argument("--tags",default=""); ap.add_argument("--publish-at",default="")
    a=ap.parse_args(); tags=[t.strip() for t in a.tags.split(",") if t.strip()]; upload(a.file,a.title,a.desc,tags,a.publish_at)

if __name__=="__main__": main()
