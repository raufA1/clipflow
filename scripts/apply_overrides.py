#!/usr/bin/env python3
import os, yaml

CFG="config/config.yaml"

def parse_bool(v, default=False):
    if v is None: return default
    return str(v).strip().lower() in ("1","true","yes","on")

def main():
    cfg=yaml.safe_load(open(CFG,"r",encoding="utf-8"))
    e=os.environ
    if e.get("CFG_LANGUAGE"): cfg["language"]=e["CFG_LANGUAGE"]
    if e.get("CFG_ENABLE_HIGHLIGHTS") is not None: cfg["enable_highlights"]=parse_bool(e.get("CFG_ENABLE_HIGHLIGHTS"), cfg.get("enable_highlights",True))
    if e.get("CFG_HL_THRESHOLD"): 
        try: cfg["highlight_threshold_sec"]=int(e["CFG_HL_THRESHOLD"])
        except: pass
    if e.get("CFG_HL_TARGETS"):
        try: cfg["highlight_targets_sec"]=[int(x.strip()) for x in e["CFG_HL_TARGETS"].split(",") if x.strip().isdigit()]
        except: pass
    ai=cfg.get("ai",{})
    if e.get("CFG_AI_ENABLED") is not None: ai["enabled"]=parse_bool(e.get("CFG_AI_ENABLED"), ai.get("enabled",True))
    if e.get("CFG_AI_PROVIDER"): ai["provider"]=e["CFG_AI_PROVIDER"]
    if e.get("CFG_AI_MODEL"): ai["model"]=e["CFG_AI_MODEL"]
    if e.get("CFG_AI_MAX_TOKENS"):
        try: ai["max_tokens"]=int(e["CFG_AI_MAX_TOKENS"])
        except: pass
    if e.get("CFG_AI_TEMPERATURE"):
        try: ai["temperature"]=float(e["CFG_AI_TEMPERATURE"])
        except: pass
    cfg["ai"]=ai
    music=cfg.get("music",{})
    if e.get("CFG_MUSIC_MODE"): music["mode"]=e["CFG_MUSIC_MODE"]
    if e.get("CFG_MUSIC_GAIN"):
        try: music["fallback_gain"]=float(e["CFG_MUSIC_GAIN"])
        except: pass
    cfg["music"]=music
    yaml.safe_dump(cfg, open(CFG,"w",encoding="utf-8"), allow_unicode=True, sort_keys=False)
    print("Applied overrides")

if __name__=="__main__": main()
