import asyncio,discord,os,threading,logging,requests as http
from discord import app_commands
from flask import Flask,redirect,request,session,jsonify
from functools import wraps
from datetime import datetime,timezone,timedelta
from html import escape

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger("bot")
BOT_TOKEN=os.environ.get("DISCORD_TOKEN","")
CLIENT_ID=os.environ.get("DISCORD_CLIENT_ID","")
CLIENT_SECRET=os.environ.get("DISCORD_CLIENT_SECRET","")
BASE_URL=os.environ.get("BASE_URL","http://localhost:8080")
REDIRECT_URI=f"{BASE_URL}/callback"
API="https://discord.com/api/v10"
app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","clave-secreta")
welcome_configs={}
def bh():return{"Authorization":f"Bot {BOT_TOKEN}"}
def uh():return{"Authorization":f"Bearer {session.get('access_token','')}"}
def require_login(f):
    @wraps(f)
    def dec(*a,**kw):
        if"access_token"not in session:return redirect("/")
        return f(*a,**kw)
    return dec

@app.route('/')
def index():
    if'access_token'in session:return redirect('/servers')
    return'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RANDOOM</title><style>*{box-sizing:border-box;margin:0;padding:0}body{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:20px}.logo{font-size:52px;font-weight:800;color:#57f287}.sub{color:#8b949e;font-size:14px;margin:12px 0 32px}.btn{background:#5865f2;color:#fff;padding:14px 28px;border-radius:10px;font-size:15px;font-weight:700;text-decoration:none;display:inline-block}</style></head><body><div class="logo">RANDOOM</div><div style="color:#57f287;font-size:13px;margin-top:6px">SUPPORT</div><div class="sub">Gestiona tu bot de Discord</div><a href="/login" class="btn">Iniciar sesion con Discord</a></body></html>'

@app.route('/login')
def login():
    return redirect(f'https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds')

@app.route('/callback')
def callback():
    code=request.args.get('code')
    if not code:return redirect('/')
    r=http.post(f'{API}/oauth2/token',data={'client_id':CLIENT_ID,'client_secret':CLIENT_SECRET,'grant_type':'authorization_code','code':code,'redirect_uri':REDIRECT_URI})
    data=r.json()
    if'access_token'not in data:return redirect('/')
    session['access_token']=data['access_token']
    session['user']=http.get(f'{API}/users/@me',headers=uh()).json()
    session['guilds']=http.get(f'{API}/users/@me/guilds',headers=uh()).json()
    return redirect('/servers')

@app.route('/logout')
def logout():
    session.clear();return redirect('/')

@app.route('/servers')
@require_login
def servers():
    user=session['user'];ug=session.get('guilds',[])
    bot_ids={g['id'] for g in http.get(f'{API}/users/@me/guilds',headers=bh()).json()}
    for g in ug:
        g['bot_installed']=g['id'] in bot_ids
        g['can_manage']=g.get('owner') or bool(int(g.get('permissions',0))&0x20)
    wb=[g for g in ug if g['bot_installed'] and g['can_manage']]
    wo=[g for g in ug if not g['bot_installed'] and g['can_manage']]
    name=escape(user.get('global_name') or user['username'])
    def gc(g,has):
        ic=f'<img src="https://cdn.discordapp.com/icons/{g["id"]}/{g["icon"]}.png?size=64" style="width:40px;height:40px;border-radius:10px">'if g.get('icon')else f'<div style="width:40px;height:40px;border-radius:10px;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:700">{g["name"][0]}</div>'
        p=int(g.get('permissions',0));role="Propietario"if g.get('owner')else("Admin"if p&0x8 else"Gestor")
        btn=f'<a href="/server/{g["id"]}" style="background:#57f287;color:#0d1117;padding:6px 12px;border-radius:7px;font-size:12px;font-weight:700;text-decoration:none">Gestionar</a>'if has else f'<a href="https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&scope=bot+applications.commands&permissions=8&guild_id={g["id"]}" target="_blank" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;padding:6px 12px;border-radius:7px;font-size:12px;font-weight:700;text-decoration:none">Agregar</a>'
        return f'<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:12px;margin-bottom:8px">{ic}<div style="flex:1;min-width:0"><div style="font-weight:600;font-size:14px">{escape(g["name"])}</div><div style="font-size:11px;color:#8b949e">{role}</div></div>{btn}</div>'
    wbh=''.join(gc(g,True)for g in wb)or'<p style="color:#8b949e;font-size:13px">Ninguno</p>'
    woh=''.join(gc(g,False)for g in wo)or'<p style="color:#8b949e;font-size:13px">Ninguno</p>'
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RANDOOM</title><style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans-serif}}.nav{{background:#161b22;border-bottom:1px solid #30363d;padding:12px 20px;display:flex;align-items:center;gap:10px}}.wrap{{max-width:860px;margin:0 auto;padding:24px 16px}}</style></head><body><nav class="nav"><span style="font-weight:800;color:#57f287">RANDOOM</span><span style="background:#57f287;color:#0d1117;font-size:10px;font-weight:800;padding:2px 8px;border-radius:20px">SUPPORT</span><a href="/logout" style="margin-left:auto;background:#21262d;border:1px solid #30363d;padding:5px 12px;border-radius:6px;font-size:12px">Salir</a></nav><div class="wrap"><h1 style="font-size:24px;font-weight:700;margin-bottom:6px">Hola, {name} !</h1><p style="color:#8b949e;font-size:14px;margin-bottom:20px">Tus servidores</p><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px"><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#57f287">{len(wb)}</div><div style="font-size:11px;color:#8b949e">Con bot</div></div><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#8b949e">{len(wo)}</div><div style="font-size:11px;color:#8b949e">Sin bot</div></div><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#58a6ff">{len(wb)+len(wo)}</div><div style="font-size:11px;color:#8b949e">Total</div></div></div>{"<div style=font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;margin-bottom:10px>BOT INSTALADO</div>"+wbh if wb else ""}{"<div style=font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;margin:20px 0 10px>SIN EL BOT</div>"+woh if wo else""}</div></body></html>'
