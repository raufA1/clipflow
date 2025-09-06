#!/usr/bin/env python3
import os, sys, argparse, requests, subprocess

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--url",required=True); ap.add_argument("--platforms",default="youtube"); a=ap.parse_args()
    ep=os.environ.get("VPS_ENDPOINT")
    if not ep: print("Missing VPS_ENDPOINT"); sys.exit(2)
    if ep.startswith("http"):
        r=requests.post(ep,json={"url":a.url,"platforms":a.platforms.split(",")},timeout=20); print("Webhook:", r.status_code, r.text)
    else:
        subprocess.run(["ssh",ep.split(":")[0],f"echo '{a.url},{a.platforms}' >> {ep.split(':')[1]}"], check=False)

if __name__=="__main__": main()
