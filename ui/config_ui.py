#!/usr/bin/env python3
import os, yaml
from flask import Flask, render_template, request, redirect, url_for, flash
from scripts.logger import tail

APP_SECRET=os.environ.get("CONFIG_UI_SECRET","change-me")
CONFIG_PATH=os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

app=Flask(__name__); app.secret_key=APP_SECRET

def load_cfg(): return yaml.safe_load(open(CONFIG_PATH,"r",encoding="utf-8"))
def save_cfg(cfg): yaml.safe_dump(cfg, open(CONFIG_PATH,"w",encoding="utf-8"), allow_unicode=True, sort_keys=False)

def load_presets():
    p=os.path.join(os.path.dirname(__file__), '..','config','presets.yaml')
    import yaml
    return yaml.safe_load(open(p,'r',encoding='utf-8')) if os.path.exists(p) else {'presets':{}}

@app.route("/", methods=["GET","POST"])
def index():
    cfg=load_cfg()
    if request.method=="POST":
        preset = request.form.get('preset','')
        if preset:
            presets = load_presets().get('presets',{})
            if preset in presets:
                save_cfg(presets[preset]); flash(f"Preset '{preset}' tətbiq olundu.","success"); return redirect(url_for("index"))
        cfg["language"]=request.form.get("language","az")
        cfg["enable_highlights"]=True if request.form.get("enable_highlights")=="on" else False
        try: cfg["highlight_threshold_sec"]=int(request.form.get("highlight_threshold_sec","90"))
        except: cfg["highlight_threshold_sec"]=90
        t=request.form.get("highlight_targets_sec","15,30,60")
        cfg["highlight_targets_sec"]=[int(x.strip()) for x in t.split(",") if x.strip().isdigit()]
        ai=cfg.get("ai",{})
        ai["enabled"]=True if request.form.get("ai_enabled")=="on" else False
        ai["provider"]=request.form.get("ai_provider","openai")
        ai["model"]=request.form.get("ai_model","gpt-4o-mini")
        try: ai["max_tokens"]=int(request.form.get("ai_max_tokens","120"))
        except: ai["max_tokens"]=120
        try: ai["temperature"]=float(request.form.get("ai_temperature","0.7"))
        except: ai["temperature"]=0.7
        cfg["ai"]=ai
        music=cfg.get("music",{})
        music["mode"]=request.form.get("music_mode","safe")
        try: music["fallback_gain"]=float(request.form.get("fallback_gain","0.25"))
        except: music["fallback_gain"]=0.25
        cfg["music"]=music
        save_cfg(cfg); flash("Konfiqurasiya yadda saxlanıldı.","success"); return redirect(url_for("index"))
    return render_template("index.html", cfg=cfg)

@app.route("/logs")
def logs():
    return render_template("logs.html", rows=tail(200))

if __name__=="__main__":
    port=int(os.environ.get("PORT","7860")); app.run(host="0.0.0.0", port=port, debug=False)
