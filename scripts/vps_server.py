#!/usr/bin/env python3
import os, json
from flask import Flask, request, jsonify

app = Flask(__name__)
QUEUE = os.environ.get("QUEUE_PATH", "scheduler/queue.jsonl")

@app.post("/enqueue")
def enqueue():
    data = request.get_json(force=True)
    url = data.get("url"); plats = data.get("platforms", ["youtube"])
    publish_at = data.get("publish_at")
    rec = {"file": url, "platforms": plats, "title": data.get("title","ClipFlow 🎱"), "caption": data.get("caption","#shorts #billiards")}
    if publish_at: rec["publish_at"] = publish_at
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","8080")))
