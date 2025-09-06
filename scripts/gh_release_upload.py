#!/usr/bin/env python3
import os, sys, requests, mimetypes, argparse

API="https://api.github.com"

def ensure_release(repo, token, tag):
    h={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    r=requests.get(f"{API}/repos/{repo}/releases/tags/{tag}", headers=h)
    if r.status_code==200: return r.json()
    r=requests.post(f"{API}/repos/{repo}/releases", headers=h, json={"tag_name":tag,"name":tag,"body":"uploads"}); r.raise_for_status(); return r.json()

def upload(repo, token, rel, file):
    h={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    url=rel["upload_url"].split("{",1)[0]; name=os.path.basename(file); mime=mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(file,"rb") as f:
        r=requests.post(f"{url}?name={name}", headers={**h,"Content-Type":mime}, data=f.read())
    if r.status_code>=300: print("Upload failed:", r.text); sys.exit(1)
    return r.json().get("browser_download_url")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--tag",default="v-uploads"); ap.add_argument("--file",required=True); a=ap.parse_args()
    repo=os.environ.get("GITHUB_REPOSITORY"); token=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not repo or not token: print("Missing GITHUB_REPOSITORY or GITHUB_TOKEN"); sys.exit(2)
    rel=ensure_release(repo, token, a.tag); url=upload(repo, token, rel, a.file); print(url)

if __name__=="__main__": main()
