#!/usr/bin/env python3
import os, json, time, threading

LOG_DIR = os.environ.get("LOG_DIR","logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "events.jsonl")
_lock = threading.Lock()

def log(event_type, **kwargs):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "type": event_type, **kwargs}
    line = json.dumps(rec, ensure_ascii=False)
    with _lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line+"\n")
    return rec

def tail(n=100):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        return [json.loads(x) for x in lines if x.strip()]
    except FileNotFoundError:
        return []
