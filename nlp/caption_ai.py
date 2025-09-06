#!/usr/bin/env python3
import os, json, yaml, requests

def load_config():
    import pathlib, yaml
    return yaml.safe_load(open(str(pathlib.Path(__file__).resolve().parents[1]/"config/config.yaml"),"r",encoding="utf-8"))

def ai_generate(language: str, events_meta: dict, variant="A"):
    if os.environ.get("OPENAI_API_KEY"):
        try:
            headers={'Authorization': f"Bearer {os.environ['OPENAI_API_KEY']}", 'Content-Type':'application/json'}
            vibe = "energetic" if len(events_meta.get("events",[]))>6 else "calm"
            style = "punchy" if variant=="A" else "friendly"
            prompt=f"Generate {language} short social caption ({style}, {vibe}) under 90 characters and 5 concise hashtags for a billiards 8-ball clip. Return JSON: captions(list), hashtags(list)."
            body={'model': load_config().get('ai',{}).get('model','gpt-4o-mini'), 'messages':[{'role':'user','content':prompt}], 'max_tokens': 180, 'temperature': 0.7 if variant=='A' else 0.9}
            r=requests.post(os.environ.get('OPENAI_BASE','https://api.openai.com/v1/chat/completions'), headers=headers, json=body, timeout=15)
            if r.status_code<300:
                txt=r.json()['choices'][0]['message']['content']
                import re, json as _json
                j=_json.loads(re.sub(r'```(json)?','',txt).strip())
                return j
        except Exception as _e:
            pass
    # Fallback
    counts={}
    for e in events_meta.get("events",[]): counts[e["type"]]=counts.get(e["type"],0)+1
    pocket=counts.get("pocket",0); shot=counts.get("shot",0)
    sample={"captions":[f"ClipFlow — {pocket} düşüş, {shot} zərbə!"],"hashtags":["#8ball","#billiards","#pool"]}
    return sample

def main(meta_json_path, out_json_path, variant="A"):
    meta=json.load(open(meta_json_path,"r",encoding="utf-8"))
    lang=load_config().get("language","az")
    res=ai_generate(lang, meta, variant=variant)
    json.dump(res, open(out_json_path,"w",encoding="utf-8"), ensure_ascii=False, indent=2); print(out_json_path)

if __name__=="__main__":
    import sys
    if len(sys.argv)<3: print("Usage: python nlp/caption_ai.py .work/video.json .work/captions.json [A|B]"); raise SystemExit(2)
    variant = sys.argv[3] if len(sys.argv)>=4 else "A"
    main(sys.argv[1], sys.argv[2], variant)
