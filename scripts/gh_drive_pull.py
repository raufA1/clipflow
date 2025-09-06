#!/usr/bin/env python3
import os, json, io, argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES=['https://www.googleapis.com/auth/drive.readonly']

def service(sa_json):
    info=json.loads(sa_json); creds=service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive','v3',credentials=creds)

def list_videos(svc, folder_id, max_files=5):
    q=f"'{folder_id}' in parents and (mimeType contains 'video' or name contains '.mp4' or name contains '.mov' or name contains '.mkv') and trashed=false"
    return svc.files().list(q=q, fields="files(id,name,modifiedTime,size)", pageSize=max_files, orderBy="modifiedTime desc").execute().get("files",[])

def download(svc, fid, name, dest):
    req=svc.files().get_media(fileId=fid); fh=io.FileIO(dest,"wb")
    downloader=MediaIoBaseDownload(fh, req); done=False
    while not done: status, done = downloader.next_chunk()
    fh.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--folder-id"); ap.add_argument("--max-files",type=int,default=5); a=ap.parse_args()
    sa=os.environ.get("GDRIVE_SA_JSON")
    if not sa: raise SystemExit("Missing GDRIVE_SA_JSON")
    if not a.folder_id: raise SystemExit("Missing --folder-id")
    svc=service(sa); files=list_videos(svc, a.folder_id, a.max_files)
    os.makedirs("inbox", exist_ok=True)
    for f in files:
        path=os.path.join("inbox", f["name"]); download(svc, f["id"], f["name"], path); print("Downloaded:", path)

if __name__=="__main__": main()
