import asyncio
import discord
import os
import threading
import logging
import requests as http
import json
from discord import app_commands
from flask import Flask, redirect, request, session, jsonify
from functools import wraps
from datetime import datetime, timezone, timedelta
from html import escape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("randoom")

BOT_TOKEN     = os.environ.get("DISCORD_TOKEN", "")
CLIENT_ID     = os.environ.get("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
BASE_URL      = os.environ.get("BASE_URL", "http://localhost:8080")
REDIRECT_URI  = f"{BASE_URL}/callback"
API           = "https://discord.com/api/v10"
PORT          = int(os.environ.get("PORT", 8080))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import sys as _sys
_sys.path.insert(0, BASE_DIR)
from config import (
    welcome_configs, save_welcome,
    verify_configs,  save_verify,
    logs_configs,    save_logs,
    ticket_configs,  save_ticket,
)

# ─── FLASK ────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "randoom-secret-2024")

def bh():
    return {"Authorization": f"Bot {BOT_TOKEN}"}

def uh():
    return {"Authorization": f"Bearer {session.get('access_token', '')}"}

def require_login(f):
    @wraps(f)
    def dec(*a, **kw):
        if "access_token" not in session:
            return redirect("/")
        return f(*a, **kw)
    return dec

CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0e13;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh}
a{text-decoration:none;color:inherit}
.nav{background:#0d1117;border-bottom:1px solid #21262d;padding:0 24px;height:54px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100}
.logo{font-size:20px;font-weight:900;color:#3cffa0;letter-spacing:-0.5px}
.badge{background:#3cffa0;color:#0b0e13;font-size:9px;font-weight:800;padding:2px 7px;border-radius:20px;letter-spacing:0.5px}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:10px}
.avatar{width:30px;height:30px;border-radius:50%;border:2px solid #21262d}
.btn-sm{background:#21262d;border:1px solid #30363d;color:#e6edf3;padding:5px 12px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer}
.btn-sm:hover{background:#30363d}
.wrap{max-width:900px;margin:0 auto;padding:28px 16px}
.card{background:#0d1117;border:1px solid #21262d;border-radius:12px;padding:20px;margin-bottom:16px}
.card h3{font-size:15px;font-weight:700;margin-bottom:4px}
.card p{font-size:12px;color:#8b949e;margin-bottom:16px}
.fg{margin-bottom:13px}
.fg label{display:block;font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:5px}
select,textarea,input[type=text],input[type=number],input[type=color]{width:100%;background:#0b0e13;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:9px 12px;font-size:13px;outline:none;font-family:inherit;transition:border-color .15s}
select:focus,textarea:focus,input:focus{border-color:#3cffa0}
textarea{resize:vertical;min-height:80px}
input[type=color]{height:38px;padding:4px 8px;cursor:pointer}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;border:none;transition:opacity .15s}
.btn:hover{opacity:.85}
.btn-g{background:#3cffa0;color:#0b0e13}
.btn-b{background:#58a6ff;color:#0b0e13}
.btn-r{background:#f85149;color:#fff}
.btn-y{background:#d29922;color:#fff}
.btn-d{background:#21262d;color:#e6edf3;border:1px solid #30363d}
.tabs{display:flex;gap:0;border-bottom:1px solid #21262d;margin-bottom:22px;overflow-x:auto}
.tab{padding:10px 16px;font-size:13px;font-weight:500;color:#8b949e;border-bottom:2px solid transparent;white-space:nowrap;cursor:pointer;background:none;border-top:none;border-left:none;border-right:none;transition:color .15s}
.tab:hover{color:#e6edf3}
.tab.active{color:#3cffa0;border-bottom-color:#3cffa0;font-weight:700}
.panel{display:none}.panel.active{display:block}
.alert{padding:10px 14px;border-radius:8px;font-size:12px;font-weight:600;margin-bottom:14px;display:none}
.alert-ok{background:rgba(60,255,160,.1);border:1px solid #3cffa0;color:#3cffa0}
.alert-err{background:rgba(248,81,73,.1);border:1px solid #f85149;color:#f85149}
.mrow{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #161b22}
.mrow:last-child{border-bottom:none}
.stat{background:#0d1117;border:1px solid #21262d;border-radius:12px;padding:18px;text-align:center}
.stat-n{font-size:28px;font-weight:800}
.stat-l{font-size:11px;color:#8b949e;margin-top:2px}
.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.cmd-row{background:#0b0e13;border:1px solid #21262d;border-radius:8px;padding:9px 13px;margin-bottom:6px;display:flex;gap:10px;align-items:center}
.cmd-row code{color:#3cffa0;font-size:12px;font-family:monospace}
.cmd-row span{color:#8b949e;font-size:11px}
.server-card{background:#0d1117;border:1px solid #21262d;border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:14px;margin-bottom:10px;transition:border-color .15s}
.server-card:hover{border-color:#30363d}
.server-icon{width:44px;height:44px;border-radius:11px;flex-shrink:0;object-fit:cover}
.server-icon-ph{width:44px;height:44px;border-radius:11px;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;color:#e6edf3;flex-shrink:0}
.tag{font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;display:inline-block}
.tag-g{background:rgba(60,255,160,.15);color:#3cffa0;border:1px solid rgba(60,255,160,.3)}
.section-title{font-size:10px;font-weight:700;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px}
@media(max-width:600px){.grid3{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}}
</style>
"""

# ─── RUTAS ────────────────────────────────────────────────────────────────────

@app.route("/ping")
def ping_route():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    if "access_token" in session:
        return redirect("/servers")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bot Dashboard</title>{CSS}</head>
<body style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px">
<div style="max-width:400px;width:100%">
<div class="logo" style="font-size:36px;margin-bottom:4px">BOT</div>
<div class="badge" style="margin-bottom:16px">DASHBOARD</div>
<p style="color:#8b949e;font-size:14px;margin-bottom:32px">Panel de control para tu bot de Discord.<br>Gestiona servidores, modera y personaliza desde aquí.</p>
<a href="/login" style="display:flex;align-items:center;justify-content:center;gap:10px;background:#5865f2;color:#fff;padding:14px 28px;border-radius:12px;font-size:15px;font-weight:700;width:100%">
<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057c.002.022.015.04.033.052a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/></svg>
Iniciar sesión con Discord
</a>
</div>
</body></html>"""

@app.route("/login")
def login():
    scope = "identify%20guilds"
    return redirect(
        f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&scope={scope}"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect("/")
    r = http.post(f"{API}/oauth2/token", data={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": REDIRECT_URI
    })
    data = r.json()
    if "access_token" not in data:
        return redirect("/")
    session["access_token"] = data["access_token"]
    session["user"] = http.get(f"{API}/users/@me", headers=uh()).json()
    return redirect("/servers")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/servers")
@require_login
def servers():
    user  = session["user"]
    name  = escape(user.get("global_name") or user["username"])
    uid   = user["id"]
    av    = user.get("avatar")
    av_url = (
        f"https://cdn.discordapp.com/avatars/{uid}/{av}.png?size=64"
        if av else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    ug = http.get(f"{API}/users/@me/guilds", headers=uh()).json()
    if not isinstance(ug, list):
        ug = []
    bot_r   = http.get(f"{API}/users/@me/guilds", headers=bh()).json()
    bot_ids = {g["id"] for g in bot_r} if isinstance(bot_r, list) else set()

    with_bot, without_bot = [], []
    for g in ug:
        perms      = int(g.get("permissions", 0))
        can_manage = g.get("owner") or bool(perms & 0x20)
        if not can_manage:
            continue
        g["bot_installed"] = g["id"] in bot_ids
        (with_bot if g["bot_installed"] else without_bot).append(g)

    def server_card(g, has_bot):
        icon_html = (
            f'<img class="server-icon" src="https://cdn.discordapp.com/icons/{g["id"]}/{g["icon"]}.png?size=64">'
            if g.get("icon") else
            f'<div class="server-icon-ph">{escape(g["name"][0])}</div>'
        )
        perms = int(g.get("permissions", 0))
        role  = "Propietario" if g.get("owner") else ("Admin" if perms & 0x8 else "Gestor")
        if has_bot:
            btn = f'<a href="/server/{g["id"]}" class="btn btn-g" style="padding:7px 14px;font-size:12px">Gestionar</a>'
        else:
            invite = (
                f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"
                f"&scope=bot+applications.commands&permissions=8&guild_id={g['id']}"
            )
            btn = f'<a href="{invite}" target="_blank" class="btn btn-d" style="padding:7px 14px;font-size:12px">Agregar bot</a>'
        return f"""<div class="server-card">
{icon_html}
<div style="flex:1;min-width:0">
  <div style="font-weight:700;font-size:14px">{escape(g["name"])}</div>
  <div style="font-size:11px;color:#8b949e;margin-top:2px">{role}</div>
</div>
{"<span class='tag tag-g'>Bot activo</span>" if has_bot else ""}
{btn}
</div>"""

    wb_html = "".join(server_card(g, True)  for g in with_bot)    or '<p style="color:#8b949e;font-size:13px;padding:12px 0">Ninguno aún.</p>'
    wo_html = "".join(server_card(g, False) for g in without_bot) or '<p style="color:#8b949e;font-size:13px;padding:12px 0">Ninguno.</p>'

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard — Servidores</title>{CSS}</head><body>
<nav class="nav">
  <span class="logo">BOT</span><span class="badge">DASHBOARD</span>
  <div class="nav-right">
    <img class="avatar" src="{av_url}">
    <span style="font-size:13px;font-weight:600">{name}</span>
    <a href="/logout" class="btn-sm">Salir</a>
  </div>
</nav>
<div class="wrap">
  <h1 style="font-size:22px;font-weight:800;margin-bottom:6px">Hola, {name}!</h1>
  <p style="color:#8b949e;font-size:13px;margin-bottom:24px">Selecciona un servidor para gestionarlo.</p>
  <div class="grid3" style="margin-bottom:28px">
    <div class="stat"><div class="stat-n" style="color:#3cffa0">{len(with_bot)}</div><div class="stat-l">Con bot</div></div>
    <div class="stat"><div class="stat-n" style="color:#8b949e">{len(without_bot)}</div><div class="stat-l">Sin bot</div></div>
    <div class="stat"><div class="stat-n" style="color:#58a6ff">{len(with_bot)+len(without_bot)}</div><div class="stat-l">Total</div></div>
  </div>
  <div class="section-title">Bot instalado</div>
  {wb_html}
  <div class="section-title" style="margin-top:24px">Sin bot — puedes agregarlo</div>
  {wo_html}
</div>
</body></html>"""


@app.route("/server/<gid>")
@require_login
def dashboard(gid):
    gr = http.get(f"{API}/guilds/{gid}", headers=bh())
    if not gr.ok:
        return redirect("/servers")
    g     = gr.json()
    gname = escape(g["name"])

    ch_r  = http.get(f"{API}/guilds/{gid}/channels", headers=bh())
    channels = sorted(
        [c for c in (ch_r.json() if ch_r.ok else []) if c["type"] == 0],
        key=lambda c: c.get("position", 0)
    )
    ro_r  = http.get(f"{API}/guilds/{gid}/roles", headers=bh())
    roles = ro_r.json() if ro_r.ok else []

    user  = session["user"]
    uname = escape(user.get("global_name") or user["username"])
    uid   = user["id"]
    av    = user.get("avatar")
    av_url = (
        f"https://cdn.discordapp.com/avatars/{uid}/{av}.png?size=64"
        if av else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    ic = (
        f'<img src="https://cdn.discordapp.com/icons/{gid}/{g["icon"]}.png?size=128" style="width:48px;height:48px;border-radius:12px">'
        if g.get("icon") else
        f'<div style="width:48px;height:48px;border-radius:12px;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:20px">{gname[0]}</div>'
    )

    copts = "".join(f'<option value="{c["id"]}">#{escape(c["name"])}</option>' for c in channels)
    ropts = "".join(
        f'<option value="{r["id"]}">@{escape(r["name"])}</option>'
        for r in sorted(roles, key=lambda r: -r.get("position", 0))
        if r["name"] != "@everyone"
    )

    gid_s           = str(gid)
    verify_cfg      = verify_configs.get(gid_s, {})
    logs_cfg        = logs_configs.get(gid_s, {})
    welcome_cfg     = welcome_configs.get(gid_s, {})
    verify_ch_sel   = verify_cfg.get("channel_id", "")
    verify_role_sel = verify_cfg.get("role_id", "")
    verify_msg_val  = escape(verify_cfg.get("message", ""))
    logs_ch_sel     = logs_cfg.get("channel_id", "")
    wel_ch_sel      = welcome_cfg.get("channel_id", "")
    embed_cfg       = welcome_cfg.get("embed_config") or {}

    def copts_sel(sel_id):
        return "".join(
            f'<option value="{c["id"]}"{"selected" if c["id"]==sel_id else ""}>#{escape(c["name"])}</option>'
            for c in channels
        )
    def ropts_sel(sel_id):
        return "".join(
            f'<option value="{r["id"]}"{"selected" if r["id"]==sel_id else ""}>@{escape(r["name"])}</option>'
            for r in sorted(roles, key=lambda r: -r.get("position", 0))
            if r["name"] != "@everyone"
        )

    all_cmds = [
        ("/ping",                              "Latencia del bot"),
        ("/hola",                              "El bot te saluda"),
        ("/ayuda",                             "Lista de comandos"),
        ("/purge [cantidad]",                  "Eliminar mensajes (1-100)"),
        ("/kick @usuario [razón]",             "Expulsar miembro"),
        ("/ban @usuario [razón]",              "Banear miembro"),
        ("/mute @usuario [minutos]",           "Silenciar miembro"),
        ("/bienvenida #canal [msg]",           "Bienvenida de texto"),
        ("/bienvenida_embed #canal ...",       "Bienvenida con embed e imagen"),
        ("/setverify #canal @rol [msg]",       "Verificación con botón"),
        ("/quitarverify",                      "Desactivar verificación"),
        ("/setlogs #canal",                    "Canal de logs"),
        ("/quitarlogs",                        "Desactivar logs"),
        ("/mensaje #canal [texto]",            "Enviar mensaje como bot"),
        ("/embed #canal ...",                  "Enviar embed"),
        ("/imagen #canal [url]",               "Enviar imagen desde URL"),
        ("/embed_imagen #canal ...",           "Embed completo con imagen"),
    ]
    cmds_html = "".join(
        f'<div class="cmd-row"><code>{c[0]}</code><span>— {c[1]}</span></div>'
        for c in all_cmds
    )

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard — {gname}</title>{CSS}</head><body>
<nav class="nav">
  <span class="logo">BOT</span><span class="badge">DASHBOARD</span>
  <span style="color:#30363d;margin:0 4px">›</span>
  <span style="font-size:13px;font-weight:700">{gname}</span>
  <div class="nav-right">
    <img class="avatar" src="{av_url}">
    <a href="/servers" class="btn-sm">Servidores</a>
    <a href="/logout" class="btn-sm">Salir</a>
  </div>
</nav>
<div class="wrap">
  <a href="/servers" style="color:#8b949e;font-size:13px;display:inline-flex;align-items:center;gap:5px;margin-bottom:18px">← Volver</a>
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px">
    {ic}
    <div>
      <div style="font-size:20px;font-weight:800">{gname}</div>
      <div style="font-size:12px;color:#8b949e;margin-top:2px">{len(channels)} canales · {len(roles)} roles</div>
    </div>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="sw(this,'resumen')">📊 Resumen</button>
    <button class="tab" onclick="sw(this,'mensajes')">💬 Mensajes</button>
    <button class="tab" onclick="sw(this,'embeds')">🖼️ Embeds</button>
    <button class="tab" onclick="sw(this,'moderacion')">🛡️ Moderación</button>
    <button class="tab" onclick="sw(this,'purge')">🗑️ Purge</button>
    <button class="tab" onclick="sw(this,'bienvenidas')">👋 Bienvenidas</button>
    <button class="tab" onclick="sw(this,'verificacion')">🔐 Verificación</button>
    <button class="tab" onclick="sw(this,'logs')">📋 Logs</button>
    <button class="tab" onclick="sw(this,'miembros')">👥 Miembros</button>
    <button class="tab" onclick="sw(this,'tickets')">🎫 Tickets</button>
  </div>

  <!-- RESUMEN -->
  <div id="p-resumen" class="panel active">
    <div class="grid2">
      <div class="stat"><div class="stat-n" style="color:#3cffa0">{len(channels)}</div><div class="stat-l">Canales de texto</div></div>
      <div class="stat"><div class="stat-n" style="color:#58a6ff">{len(roles)}</div><div class="stat-l">Roles</div></div>
    </div>
    <div class="card">
      <h3>Comandos slash disponibles</h3>
      <p>Estos comandos funcionan directamente en Discord.</p>
      {cmds_html}
    </div>
  </div>

  <!-- MENSAJES -->
  <div id="p-mensajes" class="panel">
    <div id="al-msg" class="alert"></div>
    <div class="card">
      <h3>Enviar mensaje de texto</h3>
      <p>El bot envía el texto al canal elegido.</p>
      <div class="fg"><label>Canal</label>
        <select id="msg-ch"><option value="">Selecciona un canal...</option>{copts}</select></div>
      <div class="fg"><label>Mensaje</label>
        <textarea id="msg-txt" maxlength="2000" placeholder="Escribe aquí..."></textarea></div>
      <button class="btn btn-g" onclick="sendMsg()">Enviar mensaje</button>
    </div>
  </div>

  <!-- EMBEDS -->
  <div id="p-embeds" class="panel">
    <div id="al-emb" class="alert"></div>
    <div class="card">
      <h3>Embed simple</h3>
      <p>Embed con título, descripción, color y footer opcional.</p>
      <div class="grid2">
        <div class="fg"><label>Canal</label>
          <select id="e-ch"><option value="">Canal...</option>{copts}</select></div>
        <div class="fg"><label>Color</label>
          <input type="color" id="e-col" value="#3cffa0"></div>
      </div>
      <div class="fg"><label>Título</label>
        <input type="text" id="e-title" placeholder="Título del embed"></div>
      <div class="fg"><label>Descripción</label>
        <textarea id="e-desc" placeholder="Descripción o contenido..."></textarea></div>
      <div class="fg"><label>Footer (opcional)</label>
        <input type="text" id="e-foot" placeholder="Texto del footer"></div>
      <button class="btn btn-g" onclick="sendEmbed()">Enviar embed</button>
    </div>
    <div class="card">
      <h3>Enviar imagen desde URL</h3>
      <p>Muestra una imagen en el canal usando una URL directa.</p>
      <div class="fg"><label>Canal</label>
        <select id="img-ch"><option value="">Canal...</option>{copts}</select></div>
      <div class="fg"><label>URL de la imagen</label>
        <input type="text" id="img-url" placeholder="https://ejemplo.com/imagen.png"></div>
      <div class="fg"><label>Título (opcional)</label>
        <input type="text" id="img-title" placeholder="Título encima de la imagen"></div>
      <button class="btn btn-b" onclick="sendImagen()">Enviar imagen</button>
    </div>
    <div class="card">
      <h3>Embed completo con imagen y footer</h3>
      <p>Embed con título, descripción, imagen desde URL, footer y color personalizados.</p>
      <div class="grid2">
        <div class="fg"><label>Canal</label>
          <select id="ei-ch"><option value="">Canal...</option>{copts}</select></div>
        <div class="fg"><label>Color</label>
          <input type="color" id="ei-col" value="#3cffa0"></div>
      </div>
      <div class="fg"><label>Título</label>
        <input type="text" id="ei-title" placeholder="Título del embed"></div>
      <div class="fg"><label>Descripción</label>
        <textarea id="ei-desc" placeholder="Descripción o contenido..."></textarea></div>
      <div class="fg"><label>URL de la imagen</label>
        <input type="text" id="ei-url" placeholder="https://ejemplo.com/imagen.png"></div>
      <div class="fg"><label>Footer (opcional)</label>
        <input type="text" id="ei-foot" placeholder="Texto del footer"></div>
      <button class="btn btn-g" onclick="sendEmbedImagen()">Enviar embed con imagen</button>
    </div>
    <div class="card">
      <h3>🔗 Mensaje con botones de enlace</h3>
      <p>Envía un mensaje o embed con botones que abren URLs — como Panel, Documentación, Soporte, etc.</p>
      <div class="grid2">
        <div class="fg"><label>Canal</label>
          <select id="lb-ch"><option value="">Canal...</option>{copts}</select></div>
        <div class="fg"><label>Color del embed (opcional)</label>
          <input type="color" id="lb-col" value="#5865F2"></div>
      </div>
      <div class="fg"><label>Título del embed (opcional)</label>
        <input type="text" id="lb-title" placeholder="Ej: Links de soporte — enlaces abajo."></div>
      <div class="fg"><label>Descripción (opcional)</label>
        <textarea id="lb-desc" placeholder="Descripción del mensaje..." style="min-height:60px"></textarea></div>
      <div style="font-weight:700;margin:14px 0 8px;font-size:13px">🔗 Botones de enlace (máx. 5)</div>
      <div id="lb-btns-list"><p style="color:#8b949e;font-size:12px">Sin botones aún.</p></div>
      <button class="btn btn-d" style="margin-top:6px" onclick="addLinkBtn()">+ Agregar botón</button>
      <div style="margin-top:14px">
        <button class="btn btn-g" onclick="sendLinkBtns()">📨 Enviar mensaje con botones</button>
      </div>
    </div>
  </div>

  <!-- MODERACIÓN -->
  <div id="p-moderacion" class="panel">
    <div id="al-mod" class="alert"></div>
    <div class="card">
      <h3>Moderación de miembros</h3>
      <p>Ban, kick y silencio. Carga la lista para actuar.</p>
      <div id="mod-list"><button class="btn btn-d" onclick="loadModMembers()">Cargar miembros</button></div>
    </div>
  </div>

  <!-- PURGE -->
  <div id="p-purge" class="panel">
    <div id="al-purge" class="alert"></div>
    <div class="card">
      <h3>Purge — eliminar mensajes</h3>
      <p>Borra en masa mensajes recientes de un canal (máximo 100).</p>
      <div class="fg"><label>Canal</label>
        <select id="pu-ch"><option value="">Selecciona un canal...</option>{copts}</select></div>
      <div class="fg"><label>Cantidad de mensajes</label>
        <input type="number" id="pu-amt" value="10" min="1" max="100"></div>
      <button class="btn btn-r" onclick="doPurge()">🗑️ Eliminar mensajes</button>
    </div>
  </div>

  <!-- BIENVENIDAS -->
  <div id="p-bienvenidas" class="panel">
    <div id="al-wel" class="alert"></div>
    <div class="card">
      <h3>Bienvenida de texto</h3>
      <p>Mensaje de texto cuando alguien entra. Usa <code style="color:#3cffa0">{{user}}</code> para mencionar.</p>
      <div class="fg"><label>Canal de bienvenida</label>
        <select id="wel-ch"><option value="">Selecciona un canal...</option>{copts_sel(wel_ch_sel)}</select></div>
      <div class="fg"><label>Mensaje en el canal</label>
        <textarea id="wel-msg" placeholder="¡Bienvenido {{user}} al servidor!">{escape(welcome_cfg.get("message",""))}</textarea></div>
      <div class="fg"><label>DM privado al nuevo miembro (opcional)</label>
        <textarea id="wel-dm" placeholder="Hola {{user}}, gracias por unirte!">{escape(welcome_cfg.get("dm_message",""))}</textarea></div>
      <button class="btn btn-g" onclick="saveWelcome('{gid}')">💾 Guardar bienvenida texto</button>
    </div>
    <div class="card">
      <h3>Bienvenida con Embed e Imagen</h3>
      <p>Envía un embed al entrar. Usa <code style="color:#3cffa0">{{user}}</code> en título/descripción/footer.</p>
      <div class="grid2">
        <div class="fg"><label>Canal de bienvenida</label>
          <select id="wemb-ch"><option value="">Selecciona un canal...</option>{copts_sel(wel_ch_sel)}</select></div>
        <div class="fg"><label>Color</label>
          <input type="color" id="wemb-col" value="#{embed_cfg.get('color','3cffa0')}"></div>
      </div>
      <div class="fg"><label>Título del embed</label>
        <input type="text" id="wemb-title" placeholder="¡Bienvenido al servidor, {{user}}!" value="{escape(embed_cfg.get('title',''))}"></div>
      <div class="fg"><label>Descripción</label>
        <textarea id="wemb-desc" placeholder="Hola {{user}}, bienvenido a nuestro servidor...">{escape(embed_cfg.get('description',''))}</textarea></div>
      <div class="fg"><label>URL de imagen grande (opcional)</label>
        <input type="text" id="wemb-img" placeholder="https://ejemplo.com/banner.png" value="{escape(embed_cfg.get('image_url',''))}"></div>
      <div class="fg"><label>URL de miniatura (opcional)</label>
        <input type="text" id="wemb-thumb" placeholder="https://ejemplo.com/icon.png" value="{escape(embed_cfg.get('thumbnail_url',''))}"></div>
      <div class="fg"><label>Footer (opcional)</label>
        <input type="text" id="wemb-foot" placeholder="Somos {{user}} miembros ahora!" value="{escape(embed_cfg.get('footer',''))}"></div>
      <div class="fg"><label>DM privado al nuevo miembro (opcional)</label>
        <textarea id="wemb-dm" placeholder="Hola {{user}}, bienvenido!">{escape(welcome_cfg.get("dm_message",""))}</textarea></div>
      <button class="btn btn-b" onclick="saveWelcomeEmbed('{gid}')">💾 Guardar bienvenida embed</button>
    </div>
  </div>

  <!-- VERIFICACIÓN -->
  <div id="p-verificacion" class="panel">
    <div id="al-verify" class="alert"></div>
    <div class="card">
      <h3>🔐 Verificación con botón</h3>
      <p>El bot envía un embed con un botón "✅ Verificarme". Al pulsarlo, el usuario recibe el rol automáticamente.</p>
      <div class="grid2">
        <div class="fg"><label>Canal de verificación</label>
          <select id="ver-ch"><option value="">Selecciona un canal...</option>{copts_sel(verify_ch_sel)}</select></div>
        <div class="fg"><label>Rol a asignar</label>
          <select id="ver-rol"><option value="">Selecciona un rol...</option>{ropts_sel(verify_role_sel)}</select></div>
      </div>
      <div class="fg"><label>Mensaje del embed</label>
        <textarea id="ver-msg" placeholder="Haz clic en el botón para verificarte.">{verify_msg_val}</textarea></div>
      <div style="display:flex;gap:10px;margin-top:4px">
        <button class="btn btn-g" onclick="saveVerify('{gid}')">💾 Guardar y enviar botón</button>
        {"<button class='btn btn-r' onclick='delVerify(`" + gid + "`)'>🗑️ Desactivar</button>" if verify_cfg else ""}
      </div>
      {f'<p style="margin-top:14px;font-size:12px;color:#3cffa0">✅ Configurado</p>' if verify_cfg else '<p style="margin-top:14px;font-size:12px;color:#8b949e">Sin configurar.</p>'}
    </div>
  </div>

  <!-- LOGS -->
  <div id="p-logs" class="panel">
    <div id="al-logs" class="alert"></div>
    <div class="card">
      <h3>📋 Canal de logs</h3>
      <p>Cada acción genera un embed en este canal con todos los detalles.</p>
      <div class="fg"><label>Canal de logs</label>
        <select id="log-ch"><option value="">Selecciona un canal...</option>{copts_sel(logs_ch_sel)}</select></div>
      <div style="display:flex;gap:10px;margin-top:4px">
        <button class="btn btn-g" onclick="saveLogs('{gid}')">💾 Guardar canal</button>
        {"<button class='btn btn-r' onclick='delLogs(`" + gid + "`)'>🗑️ Desactivar</button>" if logs_cfg else ""}
      </div>
      {f'<p style="margin-top:14px;font-size:12px;color:#3cffa0">✅ Canal configurado</p>' if logs_cfg else '<p style="margin-top:14px;font-size:12px;color:#8b949e">Sin configurar.</p>'}
      <div style="margin-top:16px;padding:12px 14px;background:#161b22;border-radius:8px;font-size:12px;color:#8b949e;line-height:1.8">
        <b style="color:#e6edf3">Se registran:</b><br>
        🔨 Bans &nbsp;·&nbsp; 👢 Kicks &nbsp;·&nbsp; 🔇 Mutes &nbsp;·&nbsp; 🗑️ Purges &nbsp;·&nbsp; ✅ Verificaciones<br>
        ✏️ Mensajes editados &nbsp;·&nbsp; 🎭 Cambios de rol &nbsp;·&nbsp; 📝 Cambios de apodo
      </div>
    </div>
  </div>

  <!-- TICKETS -->
  <div id="p-tickets" class="panel">
    <div id="al-tk" class="alert"></div>
    <div class="card">
      <h3>🎫 Panel de Tickets</h3>
      <p>Diseña el embed y los botones. Luego envíalo a un canal o usa <code>/ticket_panel</code>.</p>

      <div style="font-weight:700;margin:14px 0 8px;font-size:13px">📌 Configuración general</div>
      <div class="grid2">
        <div class="fg"><label>Canal del panel</label>
          <select id="tk-ch"><option value="">Selecciona canal...</option>{copts}</select></div>
        <div class="fg"><label>Categoría para tickets (opcional)</label>
          <select id="tk-cat"><option value="">Sin categoría</option>{copts}</select></div>
      </div>
      <div class="fg"><label>Rol de staff (verá todos los tickets)</label>
        <select id="tk-role"><option value="">Sin rol específico</option>{ropts}</select></div>

      <div style="font-weight:700;margin:18px 0 8px;font-size:13px">🎨 Embed del panel</div>
      <div class="grid2">
        <div class="fg"><label>Color del embed</label>
          <input type="color" id="tk-color" value="#5865F2"></div>
        <div class="fg"><label>Título</label>
          <input type="text" id="tk-title" placeholder="🎫 Help & Support"></div>
      </div>
      <div class="fg"><label>Descripción</label>
        <textarea id="tk-desc" placeholder="Si tienes alguna duda, pulsa el botón para abrir un ticket." style="min-height:80px"></textarea></div>
      <div class="grid2">
        <div class="fg"><label>Autor (nombre)</label>
          <input type="text" id="tk-author" placeholder="Nombre del autor"></div>
        <div class="fg"><label>Autor (icono URL)</label>
          <input type="text" id="tk-author-icon" placeholder="https://..."></div>
      </div>
      <div class="grid2">
        <div class="fg"><label>Imagen URL</label>
          <input type="text" id="tk-img" placeholder="https://cdn.discordapp.com/..."></div>
        <div class="fg"><label>Thumbnail URL</label>
          <input type="text" id="tk-thumb" placeholder="https://..."></div>
      </div>
      <div class="grid2">
        <div class="fg"><label>Footer texto</label>
          <input type="text" id="tk-foot" placeholder="Powered by RANHUN"></div>
        <div class="fg"><label>Footer icono URL</label>
          <input type="text" id="tk-foot-icon" placeholder="https://..."></div>
      </div>

      <div style="font-weight:700;margin:18px 0 8px;font-size:13px">🎛️ Tipo de interacción</div>
      <div style="display:flex;gap:8px;margin-bottom:14px">
        <button id="tk-mode-btn" class="btn btn-b" onclick="setTicketMode('buttons')" style="flex:1">🔘 Botones</button>
        <button id="tk-mode-sel" class="btn btn-d" onclick="setTicketMode('select')" style="flex:1">📋 Menú Select</button>
      </div>

      <div id="tk-section-buttons">
        <div style="font-weight:700;margin-bottom:8px;font-size:13px">🔘 Botones (máx. 5)</div>
        <div id="tk-btns-list"></div>
        <button class="btn btn-d" style="margin-top:8px" onclick="addTicketBtn()">+ Agregar botón</button>
      </div>

      <div id="tk-section-select" style="display:none">
        <div style="font-weight:700;margin-bottom:8px;font-size:13px">📋 Opciones del menú (máx. 25)</div>
        <div class="fg"><label>Texto del placeholder</label>
          <input type="text" id="tk-sel-placeholder" placeholder="Selecciona una opción..." oninput="updateTicketPreview()"></div>
        <div id="tk-sel-opts-list"></div>
        <button class="btn btn-d" style="margin-top:8px" onclick="addSelectOpt()">+ Agregar opción</button>
      </div>

      <div style="display:flex;gap:8px;margin-top:18px;flex-wrap:wrap">
        <button class="btn btn-g" onclick="saveTicketConfig()">💾 Guardar configuración</button>
        <button class="btn btn-b" onclick="sendTicketPanel()">📨 Enviar panel ahora</button>
      </div>
    </div>

    <div class="card" id="tk-preview-card" style="display:none">
      <div style="font-weight:700;margin-bottom:10px;font-size:13px">👁️ Vista previa del panel</div>
      <div id="tk-preview" style="background:#0b0e13;border:1px solid #21262d;border-radius:8px;padding:14px"></div>
    </div>
  </div>

  <!-- MIEMBROS / DM -->
  <div id="p-miembros" class="panel">
    <div id="al-dm" class="alert"></div>
    <div class="card">
      <h3>💬 Enviar DM directo</h3>
      <p>Busca un miembro por nombre o ID, escribe el mensaje y ve el historial del chat.</p>
      <div style="display:flex;gap:8px;margin-bottom:14px">
        <input type="text" id="dm-search" placeholder="Nombre de usuario o ID..." style="flex:1">
        <button class="btn btn-d" onclick="searchDmMember()">🔍 Buscar</button>
      </div>
      <div id="dm-result"></div>
    </div>
    <div class="card" id="dm-chat-card" style="display:none">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
        <img id="dm-chat-av" src="" style="width:38px;height:38px;border-radius:50%;object-fit:cover">
        <div>
          <div id="dm-chat-name" style="font-weight:700;font-size:14px"></div>
          <div id="dm-chat-tag" style="font-size:11px;color:#8b949e"></div>
        </div>
      </div>
      <div id="dm-history" style="background:#0b0e13;border:1px solid #21262d;border-radius:8px;padding:12px;min-height:80px;max-height:260px;overflow-y:auto;margin-bottom:12px;font-size:13px">
        <p style="color:#8b949e;font-size:12px">Cargando historial...</p>
      </div>
      <div style="display:flex;gap:8px">
        <input type="text" id="dm-msg-input" placeholder="Escribe un mensaje..." style="flex:1" onkeydown="if(event.key==='Enter')sendDmChat()">
        <button class="btn btn-b" onclick="sendDmChat()">Enviar</button>
      </div>
    </div>
  </div>
</div>

<script>
const GID = "{gid}";

function show(id, msg, ok) {{
  const e = document.getElementById(id);
  e.textContent = msg;
  e.className = "alert " + (ok ? "alert-ok" : "alert-err");
  e.style.display = "block";
  setTimeout(() => e.style.display = "none", 4500);
}}

async function post(url, data) {{
  const r = await fetch(url, {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify(data)
  }});
  return r.json();
}}

function sw(btn, name) {{
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("p-" + name).classList.add("active");
}}

async function sendMsg() {{
  const ch  = document.getElementById("msg-ch").value;
  const txt = document.getElementById("msg-txt").value.trim();
  if (!ch || !txt) return show("al-msg", "Selecciona canal y escribe el mensaje.", false);
  const r = await post("/api/msg", {{channel_id: ch, content: txt}});
  show("al-msg", r.ok ? "✅ Mensaje enviado!" : "❌ Error: " + (r.error||""), r.ok);
}}

async function sendEmbed() {{
  const ch    = document.getElementById("e-ch").value;
  const title = document.getElementById("e-title").value.trim();
  const desc  = document.getElementById("e-desc").value.trim();
  const color = parseInt(document.getElementById("e-col").value.replace("#",""), 16);
  const foot  = document.getElementById("e-foot").value.trim();
  if (!ch) return show("al-emb", "Selecciona un canal.", false);
  const r = await post("/api/embed", {{channel_id: ch, title, description: desc, color, footer: foot}});
  show("al-emb", r.ok ? "✅ Embed enviado!" : "❌ Error: " + (r.error||""), r.ok);
}}

async function sendImagen() {{
  const ch    = document.getElementById("img-ch").value;
  const url   = document.getElementById("img-url").value.trim();
  const title = document.getElementById("img-title").value.trim();
  if (!ch || !url) return show("al-emb", "Selecciona canal y escribe la URL.", false);
  const r = await post("/api/imagen", {{channel_id: ch, url, title}});
  show("al-emb", r.ok ? "✅ Imagen enviada!" : "❌ Error: " + (r.error||""), r.ok);
}}

async function sendEmbedImagen() {{
  const ch    = document.getElementById("ei-ch").value;
  const title = document.getElementById("ei-title").value.trim();
  const desc  = document.getElementById("ei-desc").value.trim();
  const url   = document.getElementById("ei-url").value.trim();
  const foot  = document.getElementById("ei-foot").value.trim();
  const color = parseInt(document.getElementById("ei-col").value.replace("#",""), 16);
  if (!ch || !url) return show("al-emb", "Selecciona canal y URL de imagen.", false);
  const r = await post("/api/embed_imagen", {{channel_id: ch, title, description: desc, image_url: url, footer: foot, color}});
  show("al-emb", r.ok ? "✅ Embed con imagen enviado!" : "❌ Error: " + (r.error||""), r.ok);
}}

async function loadModMembers() {{
  document.getElementById("mod-list").innerHTML = '<p style="color:#8b949e;font-size:13px;padding:12px 0">Cargando...</p>';
  const r  = await fetch("/api/members/" + GID);
  const ms = await r.json();
  if (!Array.isArray(ms) || ms.length === 0) {{
    document.getElementById("mod-list").innerHTML = '<p style="color:#8b949e;font-size:13px">Sin miembros.</p>';
    return;
  }}
  let html = "";
  ms.forEach(m => {{
    const u    = m.user;
    if (u.bot) return;
    const nick = esc(m.nick || u.global_name || u.username);
    const av   = u.avatar
      ? `<img src="https://cdn.discordapp.com/avatars/${{u.id}}/${{u.avatar}}.png" style="width:36px;height:36px;border-radius:50%;object-fit:cover">`
      : `<div style="width:36px;height:36px;border-radius:50%;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:700">${{u.username[0]}}</div>`;
    html += `<div class="mrow" id="mr${{u.id}}">
      ${{av}}
      <div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:600">${{nick}}</div><div style="font-size:11px;color:#8b949e">${{u.username}}</div></div>
      <button class="btn btn-r"  style="padding:5px 10px;font-size:11px" onclick="doBan('${{u.id}}','${{nick}}')">Ban</button>
      <button class="btn btn-y"  style="padding:5px 10px;font-size:11px;margin-left:4px" onclick="doKick('${{u.id}}','${{nick}}')">Kick</button>
      <button class="btn btn-d"  style="padding:5px 10px;font-size:11px;margin-left:4px" onclick="doMute('${{u.id}}','${{nick}}')">Mute</button>
    </div>`;
  }});
  document.getElementById("mod-list").innerHTML = html || '<p style="color:#8b949e;font-size:13px">Sin miembros.</p>';
}}

async function doBan(uid, name) {{
  if (!confirm("¿Banear a " + name + "?")) return;
  const reason = prompt("Razón:", "") || "Sin razón";
  const r = await post("/api/ban", {{guild_id: GID, user_id: uid, reason}});
  show("al-mod", r.ok ? "🔨 " + name + " baneado." : "❌ " + (r.error||""), r.ok);
  if (r.ok) document.getElementById("mr" + uid)?.remove();
}}

async function doKick(uid, name) {{
  if (!confirm("¿Expulsar a " + name + "?")) return;
  const reason = prompt("Razón:", "") || "Sin razón";
  const r = await post("/api/kick", {{guild_id: GID, user_id: uid, reason}});
  show("al-mod", r.ok ? "👢 " + name + " expulsado." : "❌ " + (r.error||""), r.ok);
  if (r.ok) document.getElementById("mr" + uid)?.remove();
}}

async function doMute(uid, name) {{
  const mins = prompt("¿Cuántos minutos silenciar a " + name + "?", "10");
  if (!mins) return;
  const r = await post("/api/timeout", {{guild_id: GID, user_id: uid, minutes: parseInt(mins)}});
  show("al-mod", r.ok ? "🔇 " + name + " silenciado " + mins + " min." : "❌ " + (r.error||""), r.ok);
}}

async function doPurge() {{
  const ch  = document.getElementById("pu-ch").value;
  const amt = parseInt(document.getElementById("pu-amt").value);
  if (!ch) return show("al-purge", "Selecciona un canal.", false);
  if (!confirm("¿Eliminar " + amt + " mensajes?")) return;
  const r = await post("/api/purge", {{channel_id: ch, amount: amt}});
  show("al-purge", r.ok ? "✅ " + r.deleted + " mensajes eliminados." : "❌ " + (r.error||""), r.ok);
}}

async function saveWelcome(gid) {{
  const ch  = document.getElementById("wel-ch").value;
  const msg = document.getElementById("wel-msg").value.trim();
  const dm  = document.getElementById("wel-dm").value.trim();
  if (!ch || !msg) return show("al-wel", "Selecciona canal y escribe el mensaje.", false);
  const r = await post("/api/welcome", {{guild_id: gid, channel_id: ch, message: msg, dm_message: dm, embed_config: null}});
  show("al-wel", r.ok ? "✅ Bienvenida guardada!" : "❌ " + (r.error||""), r.ok);
}}

async function saveWelcomeEmbed(gid) {{
  const ch    = document.getElementById("wemb-ch").value;
  const color = document.getElementById("wemb-col").value.replace("#","");
  const title = document.getElementById("wemb-title").value.trim();
  const desc  = document.getElementById("wemb-desc").value.trim();
  const img   = document.getElementById("wemb-img").value.trim();
  const thumb = document.getElementById("wemb-thumb").value.trim();
  const foot  = document.getElementById("wemb-foot").value.trim();
  const dm    = document.getElementById("wemb-dm").value.trim();
  if (!ch || !title) return show("al-wel", "Selecciona canal y escribe el título.", false);
  const r = await post("/api/welcome", {{
    guild_id: gid, channel_id: ch, message: "", dm_message: dm,
    embed_config: {{title, description: desc, color, image_url: img, thumbnail_url: thumb, footer: foot}}
  }});
  show("al-wel", r.ok ? "✅ Bienvenida embed guardada!" : "❌ " + (r.error||""), r.ok);
}}

async function saveVerify(gid) {{
  const ch  = document.getElementById("ver-ch").value;
  const rol = document.getElementById("ver-rol").value;
  const msg = document.getElementById("ver-msg").value.trim();
  if (!ch || !rol) return show("al-verify", "Selecciona canal y rol.", false);
  const r = await post("/api/setverify", {{guild_id: gid, channel_id: ch, role_id: rol, message: msg}});
  show("al-verify", r.ok ? "✅ Verificación configurada." : "❌ " + (r.error||""), r.ok);
}}

async function delVerify(gid) {{
  if (!confirm("¿Desactivar verificación?")) return;
  const r = await post("/api/quitarverify", {{guild_id: gid}});
  show("al-verify", r.ok ? "✅ Verificación desactivada." : "❌ " + (r.error||""), r.ok);
}}

async function saveLogs(gid) {{
  const ch = document.getElementById("log-ch").value;
  if (!ch) return show("al-logs", "Selecciona un canal.", false);
  const r = await post("/api/setlogs", {{guild_id: gid, channel_id: ch}});
  show("al-logs", r.ok ? "✅ Canal de logs guardado." : "❌ " + (r.error||""), r.ok);
}}

async function delLogs(gid) {{
  if (!confirm("¿Desactivar los logs?")) return;
  const r = await post("/api/quitarlogs", {{guild_id: gid}});
  show("al-logs", r.ok ? "✅ Logs desactivados." : "❌ " + (r.error||""), r.ok);
}}

let _dmUserId = null;

async function searchDmMember() {{
  const q = document.getElementById("dm-search").value.trim();
  if (!q) return;
  document.getElementById("dm-result").innerHTML = '<p style="color:#8b949e;font-size:12px">Buscando...</p>';
  const r  = await fetch("/api/member_search/" + GID + "?q=" + encodeURIComponent(q));
  const ms = await r.json();
  if (!Array.isArray(ms) || !ms.length) {{ document.getElementById("dm-result").innerHTML = '<p style="color:#8b949e;font-size:12px">No se encontró ningún miembro.</p>'; return; }}
  let html = "";
  ms.slice(0,8).forEach(m => {{
    const u    = m.user;
    const nick = esc(m.nick || u.global_name || u.username);
    const av   = u.avatar ? `https://cdn.discordapp.com/avatars/${{u.id}}/${{u.avatar}}.png` : "";
    const img  = av ? `<img src="${{av}}" style="width:34px;height:34px;border-radius:50%;object-fit:cover">` : `<div style="width:34px;height:34px;border-radius:50%;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px">${{u.username[0]}}</div>`;
    html += `<div class="mrow" style="cursor:pointer" onclick="openDmChat('${{u.id}}','${{nick}}','${{av}}','${{u.username}}')">
      ${{img}}
      <div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:600">${{nick}}</div><div style="font-size:11px;color:#8b949e">@${{esc(u.username)}}</div></div>
      <button class="btn btn-b" style="padding:5px 12px;font-size:11px">Chat →</button>
    </div>`;
  }});
  document.getElementById("dm-result").innerHTML = html;
}}

async function openDmChat(uid, name, av, tag) {{
  _dmUserId = uid;
  document.getElementById("dm-chat-av").src   = av || "";
  document.getElementById("dm-chat-av").style.display = av ? "block" : "none";
  document.getElementById("dm-chat-name").textContent = name;
  document.getElementById("dm-chat-tag").textContent  = "@" + tag;
  document.getElementById("dm-chat-card").style.display = "block";
  document.getElementById("dm-msg-input").focus();
  await loadDmHistory(uid);
}}

async function loadDmHistory(uid) {{
  const box = document.getElementById("dm-history");
  box.innerHTML = '<p style="color:#8b949e;font-size:12px">Cargando historial...</p>';
  try {{
    const r = await fetch("/api/dm_history/" + uid);
    if (!r.ok) {{
      box.innerHTML = '<p style="color:#f85149;font-size:12px;text-align:center">Error ' + r.status + ' al cargar historial.</p>';
      return;
    }}
    const d = await r.json();
    if (!d.ok || !d.messages || !d.messages.length) {{
      box.innerHTML = '<p style="color:#8b949e;font-size:12px;text-align:center">Sin mensajes aún — envía el primer DM.</p>';
      return;
    }}
    let html = "";
    d.messages.forEach(msg => {{
      if (!msg.content) return;
      const isBot = msg.from_bot;
      const align = isBot ? "flex-end" : "flex-start";
      const bg    = isBot ? "#1a3a2a" : "#161b22";
      const color = isBot ? "#3cffa0" : "#e6edf3";
      const name  = esc(msg.author || "?");
      const time  = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {{hour:"2-digit",minute:"2-digit"}}) : "";
      html += `<div style="display:flex;flex-direction:column;align-items:${{align}};margin-bottom:8px">
        <div style="font-size:10px;color:#8b949e;margin-bottom:2px">${{name}}${{time ? " · "+time : ""}}</div>
        <div style="background:${{bg}};color:${{color}};padding:7px 11px;border-radius:10px;max-width:85%;font-size:13px;word-break:break-word">${{esc(msg.content)}}</div>
      </div>`;
    }});
    box.innerHTML = html || '<p style="color:#8b949e;font-size:12px;text-align:center">Sin mensajes con contenido.</p>';
    box.scrollTop = box.scrollHeight;
  }} catch(e) {{
    box.innerHTML = '<p style="color:#f85149;font-size:12px;text-align:center">Error: ' + esc(String(e)) + '</p>';
  }}
}}

async function sendDmChat() {{
  if (!_dmUserId) return;
  const inp = document.getElementById("dm-msg-input");
  const txt = inp.value.trim();
  if (!txt) return;
  inp.value = "";
  const r = await post("/api/dm", {{user_id: _dmUserId, content: txt}});
  if (r.ok) {{
    await loadDmHistory(_dmUserId);
  }} else {{
    show("al-dm", "❌ " + (r.error||"No se pudo enviar"), false);
  }}
}}

function esc(s) {{ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }}

// ── LINK BUTTONS ─────────────────────────────────────────────────────────────
let _lbBtns = [];

function renderLinkBtns() {{
  const list = document.getElementById("lb-btns-list");
  if (!_lbBtns.length) {{ list.innerHTML = '<p style="color:#8b949e;font-size:12px">Sin botones aún.</p>'; return; }}
  list.innerHTML = _lbBtns.map((b,i) => `
    <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
      <input type="text" value="${{esc(b.emoji||'')}}" placeholder="Emoji" style="width:50px" oninput="_lbBtns[${{i}}].emoji=this.value">
      <input type="text" value="${{esc(b.label||'')}}" placeholder="Etiqueta" style="flex:1;min-width:90px" oninput="_lbBtns[${{i}}].label=this.value">
      <input type="text" value="${{esc(b.url||'')}}" placeholder="https://..." style="flex:2;min-width:150px" oninput="_lbBtns[${{i}}].url=this.value">
      <button class="btn btn-d" style="padding:4px 8px;font-size:11px" onclick="_lbBtns.splice(${{i}},1);renderLinkBtns()">✕</button>
    </div>`).join("");
}}

function addLinkBtn() {{
  if (_lbBtns.length >= 5) return show("al-emb","❌ Máximo 5 botones.",false);
  _lbBtns.push({{emoji:"🔗",label:"",url:""}});
  renderLinkBtns();
}}

async function sendLinkBtns() {{
  const ch = document.getElementById("lb-ch").value;
  if (!ch) return show("al-emb","❌ Selecciona un canal.",false);
  const validBtns = _lbBtns.filter(b => b.label && b.url);
  if (!validBtns.length) return show("al-emb","❌ Agrega al menos un botón con etiqueta y URL.",false);
  const r = await post("/api/link_buttons", {{
    channel_id: ch,
    color: parseInt(document.getElementById("lb-col").value.replace("#",""),16),
    title: document.getElementById("lb-title").value.trim(),
    description: document.getElementById("lb-desc").value.trim(),
    buttons: validBtns
  }});
  show("al-emb", r.ok ? "✅ Mensaje con botones enviado." : "❌ " + (r.error||""), r.ok);
}}

// ── TICKETS ──────────────────────────────────────────────────────────────────
let _tkBtns = [];
let _tkSelOpts = [];
let _tkMode = "buttons";
const _COLORS_MAP = {{blurple:"#5865F2",green:"#57F287",red:"#ED4245",gray:"#4F545C"}};

function setTicketMode(mode) {{
  _tkMode = mode;
  document.getElementById("tk-section-buttons").style.display = mode==="buttons" ? "" : "none";
  document.getElementById("tk-section-select").style.display  = mode==="select"  ? "" : "none";
  document.getElementById("tk-mode-btn").className = "btn " + (mode==="buttons" ? "btn-b" : "btn-d");
  document.getElementById("tk-mode-sel").className = "btn " + (mode==="select"  ? "btn-b" : "btn-d");
  updateTicketPreview();
}}

function addSelectOpt() {{
  _tkSelOpts.push({{emoji:"🎧",label:"",description:""}});
  renderSelectOpts();
}}

function renderSelectOpts() {{
  const list = document.getElementById("tk-sel-opts-list");
  if (!_tkSelOpts.length) {{ list.innerHTML = '<p style="color:#8b949e;font-size:12px">Sin opciones aún.</p>'; return; }}
  list.innerHTML = _tkSelOpts.map((o,i) => `
    <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
      <input type="text" value="${{esc(o.emoji||'')}}" placeholder="Emoji" style="width:50px" oninput="_tkSelOpts[${{i}}].emoji=this.value;updateTicketPreview()">
      <input type="text" value="${{esc(o.label||'')}}" placeholder="Nombre" style="flex:1;min-width:100px" oninput="_tkSelOpts[${{i}}].label=this.value;updateTicketPreview()">
      <input type="text" value="${{esc(o.description||'')}}" placeholder="Descripción (opcional)" style="flex:2;min-width:130px" oninput="_tkSelOpts[${{i}}].description=this.value">
      <button class="btn btn-d" style="padding:4px 8px;font-size:11px" onclick="_tkSelOpts.splice(${{i}},1);renderSelectOpts();updateTicketPreview()">✕</button>
    </div>`).join("");
}}

async function loadTicketConfig() {{
  const r = await fetch("/api/ticket_config/" + GID);
  const d = await r.json();
  if (!d.ok) return;
  const c = d.config;
  document.getElementById("tk-ch").value    = c.channel_id    || "";
  document.getElementById("tk-cat").value   = c.category_id   || "";
  document.getElementById("tk-role").value  = c.staff_role_id || "";
  const emb = c.embed || {{}};
  document.getElementById("tk-color").value  = emb.color       || "#5865F2";
  document.getElementById("tk-title").value  = emb.title       || "";
  document.getElementById("tk-desc").value   = emb.description || "";
  document.getElementById("tk-author").value = emb.author_name || "";
  document.getElementById("tk-author-icon").value = emb.author_icon_url || "";
  document.getElementById("tk-img").value    = emb.image_url   || "";
  document.getElementById("tk-thumb").value  = emb.thumbnail_url || "";
  document.getElementById("tk-foot").value   = emb.footer_text || "";
  document.getElementById("tk-foot-icon").value = emb.footer_icon_url || "";
  _tkBtns    = c.buttons      || [];
  _tkSelOpts = c.select_options || [];
  const ph   = c.select_placeholder || "";
  if (document.getElementById("tk-sel-placeholder")) document.getElementById("tk-sel-placeholder").value = ph;
  setTicketMode(c.interaction_mode || "buttons");
  renderTicketBtns();
  renderSelectOpts();
  updateTicketPreview();
}}

function renderTicketBtns() {{
  const list = document.getElementById("tk-btns-list");
  if (!_tkBtns.length) {{ list.innerHTML = '<p style="color:#8b949e;font-size:12px">Sin botones aún.</p>'; return; }}
  const colorNames = {{blurple:"Azul",green:"Verde",red:"Rojo",gray:"Gris"}};
  list.innerHTML = _tkBtns.map((b,i) => {{
    const opts = ["blurple","green","red","gray"].map(c =>
      `<option value="${{c}}"${{c===b.color?" selected":""}}>${{colorNames[c]}}</option>`
    ).join("");
    return `<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
      <input type="text" value="${{esc(b.emoji||'')}}" placeholder="Emoji" style="width:54px" oninput="_tkBtns[${{i}}].emoji=this.value;updateTicketPreview()">
      <input type="text" value="${{esc(b.label||'')}}" placeholder="Nombre" style="flex:1;min-width:100px" oninput="_tkBtns[${{i}}].label=this.value;updateTicketPreview()">
      <select onchange="_tkBtns[${{i}}].color=this.value;updateTicketPreview()" style="width:100px">${{opts}}</select>
      <button class="btn btn-d" style="padding:4px 10px;font-size:11px" onclick="_tkBtns.splice(${{i}},1);renderTicketBtns();updateTicketPreview()">✕</button>
    </div>`;
  }}).join("");
}}

function addTicketBtn() {{
  if (_tkBtns.length >= 5) return show("al-tk","❌ Máximo 5 botones.",false);
  _tkBtns.push({{label:"Soporte",emoji:"🎧",color:"blurple"}});
  renderTicketBtns();
  updateTicketPreview();
}}

function getTicketData() {{
  return {{
    guild_id:             GID,
    channel_id:           document.getElementById("tk-ch").value,
    category_id:          document.getElementById("tk-cat").value,
    staff_role_id:        document.getElementById("tk-role").value,
    interaction_mode:     _tkMode,
    select_placeholder:   (document.getElementById("tk-sel-placeholder")||{{}}).value || "Selecciona una opción...",
    embed: {{
      color:           document.getElementById("tk-color").value,
      title:           document.getElementById("tk-title").value,
      description:     document.getElementById("tk-desc").value,
      author_name:     document.getElementById("tk-author").value,
      author_icon_url: document.getElementById("tk-author-icon").value,
      image_url:       document.getElementById("tk-img").value,
      thumbnail_url:   document.getElementById("tk-thumb").value,
      footer_text:     document.getElementById("tk-foot").value,
      footer_icon_url: document.getElementById("tk-foot-icon").value,
    }},
    buttons:        _tkBtns,
    select_options: _tkSelOpts,
  }};
}}

async function saveTicketConfig() {{
  const d = getTicketData();
  const r = await post("/api/ticket_config", d);
  show("al-tk", r.ok ? "✅ Configuración guardada." : "❌ " + (r.error||""), r.ok);
}}

async function sendTicketPanel() {{
  const d = getTicketData();
  if (!d.channel_id) return show("al-tk","❌ Selecciona un canal primero.",false);
  if (!d.buttons.length) return show("al-tk","❌ Agrega al menos un botón.",false);
  const r = await post("/api/send_ticket_panel", d);
  show("al-tk", r.ok ? "✅ Panel enviado al canal." : "❌ " + (r.error||""), r.ok);
}}

function updateTicketPreview() {{
  const card = document.getElementById("tk-preview-card");
  const prev = document.getElementById("tk-preview");
  card.style.display = "block";
  const color = document.getElementById("tk-color").value;
  const title = esc(document.getElementById("tk-title").value || "🎫 Help & Support");
  const desc  = esc(document.getElementById("tk-desc").value || "Pulsa un botón para abrir tu ticket.");
  const auth  = esc(document.getElementById("tk-author").value);
  const foot  = esc(document.getElementById("tk-foot").value);
  const img   = document.getElementById("tk-img").value;
  const thumb = document.getElementById("tk-thumb").value;

  let interactionHtml = "";
  if (_tkMode === "buttons") {{
    const btns = _tkBtns.map(b => `<span style="background:${{_COLORS_MAP[b.color]||'#5865F2'}};color:#fff;padding:6px 14px;border-radius:4px;font-size:12px;font-weight:700">${{esc(b.emoji||'')}} ${{esc(b.label||'')}}</span>`).join(" ");
    if (btns) interactionHtml = `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">${{btns}}</div>`;
  }} else {{
    const ph   = esc((document.getElementById("tk-sel-placeholder")||{{}}).value || "Selecciona una opción...");
    const opts = _tkSelOpts.filter(o=>o.label).map(o => `<div style="padding:8px 12px;border-radius:6px;background:#21262d;margin-bottom:4px;font-size:13px">${{esc(o.emoji||'')}} <b>${{esc(o.label)}}</b>${{o.description ? ` <span style="color:#8b949e;font-size:11px">— ${{esc(o.description)}}</span>` : ""}}</div>`).join("");
    interactionHtml = `<div style="margin-top:10px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px">
      <div style="font-size:12px;color:#8b949e;margin-bottom:8px">▾ ${{ph}}</div>
      ${{opts || '<div style="color:#8b949e;font-size:12px">Sin opciones aún</div>'}}
    </div>`;
  }}

  prev.innerHTML = `<div style="border-left:4px solid ${{color}};padding:10px 12px;background:#161b22;border-radius:0 8px 8px 0">
    ${{auth ? `<div style="font-size:11px;color:#8b949e;margin-bottom:4px">👤 ${{auth}}</div>` : ""}}
    <div style="font-weight:700;margin-bottom:6px">${{title}}</div>
    <div style="font-size:13px;color:#8b949e;margin-bottom:8px;white-space:pre-wrap">${{desc}}</div>
    ${{thumb ? `<img src="${{esc(thumb)}}" style="float:right;width:60px;height:60px;border-radius:6px;object-fit:cover">` : ""}}
    ${{img ? `<img src="${{esc(img)}}" style="width:100%;border-radius:6px;margin:6px 0">` : ""}}
    ${{foot ? `<div style="font-size:11px;color:#8b949e;border-top:1px solid #21262d;padding-top:6px;margin-top:8px">${{foot}}</div>` : ""}}
  </div>${{interactionHtml}}`;
}}

// Cargar config de tickets al entrar al tab
document.addEventListener("DOMContentLoaded", () => {{
  const tkTab = document.querySelector('[onclick*="tickets"]');
  if (tkTab) tkTab.addEventListener("click", () => {{ if(!_tkBtns.length) loadTicketConfig(); }}, {{once:true}});
}});
</script>
</body></html>"""


# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route("/api/msg", methods=["POST"])
@require_login
def api_msg():
    d = request.json
    r = http.post(f"{API}/channels/{d['channel_id']}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json={"content": d["content"]})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/embed", methods=["POST"])
@require_login
def api_embed():
    d = request.json
    embed = {"title": d.get("title",""), "description": d.get("description",""),
             "color": d.get("color", 0x3CFFA0)}
    if d.get("footer"):
        embed["footer"] = {"text": d["footer"]}
    r = http.post(f"{API}/channels/{d['channel_id']}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json={"embeds": [embed]})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/imagen", methods=["POST"])
@require_login
def api_imagen():
    d = request.json
    embed = {"color": 0x3CFFA0, "image": {"url": d["url"]}}
    if d.get("title"):
        embed["title"] = d["title"]
    r = http.post(f"{API}/channels/{d['channel_id']}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json={"embeds": [embed]})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/embed_imagen", methods=["POST"])
@require_login
def api_embed_imagen():
    d = request.json
    embed = {
        "title":       d.get("title",""),
        "description": d.get("description",""),
        "color":       d.get("color", 0x3CFFA0),
        "image":       {"url": d["image_url"]}
    }
    if d.get("footer"):
        embed["footer"] = {"text": d["footer"]}
    r = http.post(f"{API}/channels/{d['channel_id']}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json={"embeds": [embed]})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/dm", methods=["POST"])
@require_login
def api_dm():
    d  = request.json
    ch = http.post(f"{API}/users/@me/channels",
                   headers={**bh(), "Content-Type": "application/json"},
                   json={"recipient_id": d["user_id"]})
    if not ch.ok:
        return jsonify({"ok": False, "error": "No se pudo abrir DM"})
    cid = ch.json()["id"]
    r   = http.post(f"{API}/channels/{cid}/messages",
                    headers={**bh(), "Content-Type": "application/json"},
                    json={"content": d["content"]})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/dm_history/<user_id>", methods=["GET"])
@require_login
def api_dm_history(user_id):
    try:
        ch = http.post(f"{API}/users/@me/channels",
                       headers={**bh(), "Content-Type": "application/json"},
                       json={"recipient_id": user_id},
                       timeout=8)
        if not ch.ok:
            logger.warning(f"dm_history: no pude abrir DM con {user_id}: {ch.status_code} {ch.text[:200]}")
            return jsonify({"ok": False, "messages": [], "error": f"Discord {ch.status_code}"})
        ch_data = ch.json()
        cid = ch_data.get("id")
        if not cid:
            return jsonify({"ok": False, "messages": [], "error": "Sin canal DM"})
        msgs = http.get(f"{API}/channels/{cid}/messages?limit=25",
                        headers=bh(), timeout=8)
        if not msgs.ok:
            logger.warning(f"dm_history: no pude leer mensajes del canal {cid}: {msgs.status_code}")
            return jsonify({"ok": True, "messages": []})
        raw    = msgs.json()
        me_id  = str(client.user.id) if client.user else None
        result = []
        for m in reversed(raw):
            content = m.get("content", "")
            if not content and m.get("embeds"):
                content = "[embed]"
            elif not content and m.get("attachments"):
                content = "[archivo adjunto]"
            if not content:
                continue
            result.append({
                "author":    m["author"].get("global_name") or m["author"].get("username", "?"),
                "content":   content,
                "timestamp": m.get("timestamp", ""),
                "from_bot":  m["author"]["id"] == me_id
            })
        return jsonify({"ok": True, "messages": result})
    except Exception as e:
        logger.error(f"dm_history error: {e}")
        return jsonify({"ok": False, "messages": [], "error": str(e)})


@app.route("/api/ban", methods=["POST"])
@require_login
def api_ban():
    d = request.json
    r = http.put(f"{API}/guilds/{d['guild_id']}/bans/{d['user_id']}",
                 headers={**bh(), "Content-Type": "application/json"},
                 json={"delete_message_days": 0, "reason": d.get("reason","Sin razón")})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/kick", methods=["POST"])
@require_login
def api_kick():
    d = request.json
    r = http.delete(f"{API}/guilds/{d['guild_id']}/members/{d['user_id']}",
                    headers=bh())
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/timeout", methods=["POST"])
@require_login
def api_timeout():
    d     = request.json
    until = (datetime.now(timezone.utc) + timedelta(minutes=int(d.get("minutes", 10)))).isoformat()
    r     = http.patch(f"{API}/guilds/{d['guild_id']}/members/{d['user_id']}",
                       headers={**bh(), "Content-Type": "application/json"},
                       json={"communication_disabled_until": until})
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/purge", methods=["POST"])
@require_login
def api_purge():
    d      = request.json
    amount = min(int(d.get("amount", 10)), 100)
    msgs_r = http.get(f"{API}/channels/{d['channel_id']}/messages?limit={amount}", headers=bh())
    if not msgs_r.ok:
        return jsonify({"ok": False, "error": "No se pudieron obtener mensajes"})
    ids = [m["id"] for m in msgs_r.json()]
    if not ids:
        return jsonify({"ok": True, "deleted": 0})
    if len(ids) == 1:
        r = http.delete(f"{API}/channels/{d['channel_id']}/messages/{ids[0]}", headers=bh())
        return jsonify({"ok": r.ok, "deleted": 1 if r.ok else 0})
    r = http.post(f"{API}/channels/{d['channel_id']}/messages/bulk-delete",
                  headers={**bh(), "Content-Type": "application/json"},
                  json={"messages": ids})
    return jsonify({"ok": r.ok, "deleted": len(ids) if r.ok else 0,
                    "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/welcome", methods=["POST"])
@require_login
def api_welcome():
    d   = request.json
    gid = str(d["guild_id"])
    welcome_configs[gid] = {
        "channel_id":   d["channel_id"],
        "message":      d.get("message", ""),
        "dm_message":   d.get("dm_message", ""),
        "embed_config": d.get("embed_config")
    }
    save_welcome(welcome_configs)
    return jsonify({"ok": True})


@app.route("/api/setverify", methods=["POST"])
@require_login
def api_setverify():
    d   = request.json
    gid = str(d["guild_id"])
    cfg = {
        "channel_id": d["channel_id"],
        "role_id":    d["role_id"],
        "message":    d.get("message", "Haz clic en el botón para verificarte y acceder al servidor.")
    }
    verify_configs[gid] = cfg
    save_verify(verify_configs)
    payload = {
        "embeds": [{
            "title":       "🔐 Verificación",
            "description": cfg["message"],
            "color":       0x3CFFA0,
            "footer":      {"text": "Pulsa el botón para obtener acceso al servidor."}
        }],
        "components": [{
            "type": 1,
            "components": [{
                "type":      2,
                "style":     3,
                "label":     "✅ Verificarme",
                "custom_id": "randoom_verify_button"
            }]
        }]
    }
    r = http.post(
        f"{API}/channels/{d['channel_id']}/messages",
        headers={**bh(), "Content-Type": "application/json"},
        json=payload
    )
    return jsonify({"ok": r.ok, "error": r.json().get("message", "") if not r.ok else None})


@app.route("/api/quitarverify", methods=["POST"])
@require_login
def api_quitarverify():
    gid = str(request.json["guild_id"])
    if gid in verify_configs:
        del verify_configs[gid]
        save_verify(verify_configs)
    return jsonify({"ok": True})


@app.route("/api/setlogs", methods=["POST"])
@require_login
def api_setlogs():
    d   = request.json
    gid = str(d["guild_id"])
    logs_configs[gid] = {"channel_id": d["channel_id"]}
    save_logs(logs_configs)
    return jsonify({"ok": True})


@app.route("/api/quitarlogs", methods=["POST"])
@require_login
def api_quitarlogs():
    gid = str(request.json["guild_id"])
    if gid in logs_configs:
        del logs_configs[gid]
        save_logs(logs_configs)
    return jsonify({"ok": True})


@app.route("/api/ticket_config/<gid>")
@require_login
def api_get_ticket_config(gid):
    return jsonify({"ok": True, "config": ticket_configs.get(gid, {})})


@app.route("/api/link_buttons", methods=["POST"])
@require_login
def api_link_buttons():
    d      = request.json
    ch_id  = d.get("channel_id")
    if not ch_id:
        return jsonify({"ok": False, "error": "Sin canal"})
    btns   = d.get("buttons", [])
    if not btns:
        return jsonify({"ok": False, "error": "Sin botones"})
    payload: dict = {}
    if d.get("title") or d.get("description"):
        emb: dict = {"color": d.get("color", 0x5865F2)}
        if d.get("title"):       emb["title"]       = d["title"]
        if d.get("description"): emb["description"] = d["description"]
        payload["embeds"] = [emb]
    row = []
    for b in btns[:5]:
        btn = {"type": 2, "style": 5, "label": b.get("label", "Link"), "url": b.get("url", "")}
        if b.get("emoji"):
            btn["emoji"] = {"name": b["emoji"]}
        row.append(btn)
    payload["components"] = [{"type": 1, "components": row}]
    r = http.post(f"{API}/channels/{ch_id}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json=payload)
    return jsonify({"ok": r.ok, "error": r.json().get("message","") if not r.ok else None})


@app.route("/api/ticket_config", methods=["POST"])
@require_login
def api_save_ticket_config():
    d   = request.json
    gid = str(d["guild_id"])
    ticket_configs[gid] = {
        "channel_id":          d.get("channel_id", ""),
        "category_id":         d.get("category_id", ""),
        "staff_role_id":       d.get("staff_role_id", ""),
        "interaction_mode":    d.get("interaction_mode", "buttons"),
        "select_placeholder":  d.get("select_placeholder", "Selecciona una opción..."),
        "embed":               d.get("embed", {}),
        "buttons":             d.get("buttons", []),
        "select_options":      d.get("select_options", []),
    }
    save_ticket(ticket_configs)
    return jsonify({"ok": True})


@app.route("/api/send_ticket_panel", methods=["POST"])
@require_login
def api_send_ticket_panel():
    d   = request.json
    gid = str(d["guild_id"])
    cfg = {
        "channel_id":         d.get("channel_id", ""),
        "category_id":        d.get("category_id", ""),
        "staff_role_id":      d.get("staff_role_id", ""),
        "interaction_mode":   d.get("interaction_mode", "buttons"),
        "select_placeholder": d.get("select_placeholder", "Selecciona una opción..."),
        "embed":              d.get("embed", {}),
        "buttons":            d.get("buttons", []),
        "select_options":     d.get("select_options", []),
    }
    ticket_configs[gid] = cfg
    save_ticket(ticket_configs)

    ch_id   = cfg.get("channel_id")
    if not ch_id:
        return jsonify({"ok": False, "error": "Sin canal seleccionado"})
    emb_cfg = cfg.get("embed", {})
    try:
        color = int(emb_cfg.get("color", "#5865F2").lstrip("#"), 16)
    except ValueError:
        color = 0x5865F2

    embed_payload: dict = {
        "title":       emb_cfg.get("title", "🎫 Soporte"),
        "description": emb_cfg.get("description", "Pulsa un botón para abrir tu ticket."),
        "color":       color,
    }
    if emb_cfg.get("author_name"):
        embed_payload["author"] = {"name": emb_cfg["author_name"],
                                   "icon_url": emb_cfg.get("author_icon_url", "")}
    if emb_cfg.get("thumbnail_url"):
        embed_payload["thumbnail"] = {"url": emb_cfg["thumbnail_url"]}
    if emb_cfg.get("image_url"):
        embed_payload["image"] = {"url": emb_cfg["image_url"]}
    if emb_cfg.get("footer_text"):
        embed_payload["footer"] = {"text": emb_cfg["footer_text"],
                                   "icon_url": emb_cfg.get("footer_icon_url", "")}

    style_map = {"blurple": 1, "gray": 2, "green": 3, "red": 4}
    components = []
    mode = cfg.get("interaction_mode", "buttons")

    if mode == "select":
        sel_opts = cfg.get("select_options", [])
        if sel_opts:
            options = []
            for i, opt in enumerate(sel_opts[:25]):
                o: dict = {
                    "label":       opt.get("label", f"Opción {i+1}"),
                    "value":       f"ticket_sel_{gid}_{i}",
                    "description": opt.get("description", "")[:100],
                }
                if opt.get("emoji"):
                    o["emoji"] = {"name": opt["emoji"]}
                options.append(o)
            select_comp: dict = {
                "type":        3,
                "custom_id":   f"ticket_select_{gid}",
                "placeholder": cfg.get("select_placeholder", "Selecciona una opción..."),
                "options":     options,
            }
            components.append({"type": 1, "components": [select_comp]})
    else:
        btns = cfg.get("buttons", [])
        if btns:
            row_btns = []
            for i, b in enumerate(btns[:5]):
                btn = {
                    "type":      2,
                    "style":     style_map.get(b.get("color", "blurple"), 1),
                    "label":     b.get("label", f"Ticket {i+1}"),
                    "custom_id": f"ticket_open_{gid}_{i}",
                }
                if b.get("emoji"):
                    btn["emoji"] = {"name": b["emoji"]}
                row_btns.append(btn)
            components.append({"type": 1, "components": row_btns})

    payload = {"embeds": [embed_payload]}
    if components:
        payload["components"] = components

    r = http.post(f"{API}/channels/{ch_id}/messages",
                  headers={**bh(), "Content-Type": "application/json"},
                  json=payload)
    if not r.ok:
        err = r.json().get("message", "Error enviando panel")
        return jsonify({"ok": False, "error": err})
    return jsonify({"ok": True})


@app.route("/api/members/<gid>")
@require_login
def api_members(gid):
    r = http.get(f"{API}/guilds/{gid}/members?limit=1000", headers=bh())
    return jsonify(r.json() if r.ok else [])


@app.route("/api/member_search/<gid>")
@require_login
def api_member_search(gid):
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    # búsqueda por ID directa
    if q.isdigit():
        r = http.get(f"{API}/guilds/{gid}/members/{q}", headers=bh())
        if r.ok:
            return jsonify([r.json()])
        # intenta usuario global
        ru = http.get(f"{API}/users/{q}", headers=bh())
        if ru.ok:
            u = ru.json()
            return jsonify([{"user": u, "nick": None, "roles": []}])
        return jsonify([])
    # búsqueda por nombre con endpoint nativo de Discord
    r = http.get(f"{API}/guilds/{gid}/members/search?query={q}&limit=10", headers=bh())
    return jsonify(r.json() if r.ok else [])


@app.route("/health")
def health():
    from bot import client as bot_client
    return jsonify({
        "status": "ok",
        "bot": str(bot_client.user) if bot_client.is_ready() else "connecting"
    }), 200


# ─── DISCORD BOT ──────────────────────────────────────────────────────────────
from bot import client as bot_client


def run_bot():
    if not BOT_TOKEN:
        logger.warning("DISCORD_TOKEN no definido — bot no iniciado.")
        return
    import time as _time
    delay = 2
    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_client.start(BOT_TOKEN, reconnect=True))
        except Exception as e:
            logger.error(f"Bot caído: {e}. Reconectando en {delay}s...")
            _time.sleep(delay)
            delay = min(delay * 2, 60)
        finally:
            try:
                loop.close()
            except Exception:
                pass


if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=PORT)
