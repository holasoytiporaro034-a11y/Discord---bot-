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
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RANDOOM</title><style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans-serif}}.nav{{background:#161b22;border-bottom:1px solid #30363d;padding:12px 20px;display:flex;align-items:center;gap:10px}}.wrap{{max-width:860px;margin:0 auto;padding:24px 16px}}</style></head><body><nav class="nav"><span style="font-weight:800;color:#57f287">RANDOOM</span><span style="background:#57f287;color:#0d1117;font-size:10px;font-weight:800;padding:2px 8px;border-radius:20px">SUPPORT</span><a href="/logout" style="margin-left:auto;background:#21262d;border:1px solid #30363d;padding:5px 12px;border-radius:6px;font-size:12px">Salir</a></nav><div class="wrap"><h1 style="font-size:24px;font-weight:700;margin-bottom:6px">Hola, {name} !</h1><p style="color:#8b949e;font-size:14px;margin-bottom:20px">Tus servidores</p><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px"><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#57f287">{len(wb)}</div><div style="font-size:11px;color:#8b949e">Con bot</div></div><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#8b949e">{len(wo)}</div><div style="font-size:11px;color:#8b949e">Sin bot</div></div><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;text-align:center"><div style="font-size:26px;font-weight:700;color:#58a6ff">{len(wb)+len(wo)}</div><div style="font-size:11px;color:#8b949e">Total</div></div></div>{"<div style=font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;margin-bottom:10px>BOT INSTALADO</div>"+wbh if wb else ""}{"<div style=font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;margin:20px 0 10px>SIN EL BOT</div>"+woh if wo else""}</div></body></html>'@app.route('/server/<gid>')
@require_login
def dashboard(gid):
    gr=http.get(f'{API}/guilds/{gid}',headers=bh())
    if not gr.ok:return redirect('/servers')
    g=gr.json();gname=escape(g['name'])
    ch=http.get(f'{API}/guilds/{gid}/channels',headers=bh())
    channels=sorted([c for c in(ch.json()if ch.ok else[])if c['type']==0],key=lambda c:c.get('position',0))
    ro=http.get(f'{API}/guilds/{gid}/roles',headers=bh())
    roles=ro.json()if ro.ok else[]
    user=session['user'];uname=escape(user.get('global_name')or user['username'])
    copts=''.join(f'<option value="{c["id"]}">#{c["name"]}</option>'for c in channels)
    ic=f'<img src="https://cdn.discordapp.com/icons/{gid}/{g["icon"]}.png?size=64" style="width:42px;height:42px;border-radius:10px">'if g.get('icon')else f'<div style="width:42px;height:42px;border-radius:10px;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px">{g["name"][0]}</div>'
    cmds=[("/ping","Latencia"),("/hola","Saludo"),("/ayuda","Comandos"),("/ban @user","Banear"),("/kick @user","Expulsar"),("/timeout @user [min]","Silenciar"),("/purge [n]","Eliminar msgs"),("/dm @user [msg]","Enviar DM")]
    ch_html=''.join(f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:7px;padding:8px 12px;margin-bottom:6px;display:flex;gap:8px"><code style="color:#57f287;font-size:12px">{c[0]}</code><span style="color:#8b949e;font-size:11px">- {c[1]}</span></div>'for c in cmds)
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RANDOOM - {gname}</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans-serif}}
.nav{{background:#161b22;border-bottom:1px solid #30363d;padding:12px 20px;display:flex;align-items:center;gap:10px;position:sticky;top:0;z-index:10}}
.wrap{{max-width:860px;margin:0 auto;padding:20px 16px}}
.tabs{{display:flex;gap:2px;border-bottom:1px solid #30363d;margin-bottom:20px;overflow-x:auto;padding-bottom:1px}}
.tab{{padding:9px 14px;font-size:13px;font-weight:500;color:#8b949e;border-bottom:2px solid transparent;white-space:nowrap;cursor:pointer;background:none;border-top:none;border-left:none;border-right:none}}
.tab.active{{color:#57f287;border-bottom-color:#57f287}}
.panel{{display:none}}.panel.active{{display:block}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:18px;margin-bottom:14px}}
.fg{{margin-bottom:12px}}.fg label{{display:block;font-size:11px;color:#8b949e;margin-bottom:5px}}
select,textarea,input[type=text],input[type=number]{{width:100%;background:#0d1117;border:1px solid #30363d;border-radius:7px;color:#e6edf3;padding:9px 11px;font-size:13px;outline:none;font-family:inherit}}
select:focus,textarea:focus,input:focus{{border-color:#57f287}}textarea{{resize:vertical;min-height:76px}}
.btn{{display:inline-flex;align-items:center;gap:5px;padding:7px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;border:none}}
.bg{{background:#57f287;color:#0d1117}}.bb{{background:#58a6ff;color:#0d1117}}.br{{background:#f85149;color:#fff}}.bd{{background:#21262d;color:#e6edf3;border:1px solid #30363d}}
.alert{{padding:9px 12px;border-radius:7px;font-size:12px;margin-bottom:12px;display:none}}
.as{{background:rgba(87,242,135,.12);border:1px solid #57f287;color:#57f287}}.ae{{background:rgba(248,81,73,.12);border:1px solid #f85149;color:#f85149}}
.mrow{{display:flex;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid #21262d}}
</style></head><body>
<nav class="nav"><span style="font-weight:800;color:#57f287">RANDOOM</span><span style="background:#57f287;color:#0d1117;font-size:10px;font-weight:800;padding:2px 8px;border-radius:20px">SUPPORT</span>
<span style="color:#8b949e;font-size:13px;margin:0 4px">/</span><span style="font-size:13px;font-weight:600">{gname}</span>
<a href="/logout" style="margin-left:auto;background:#21262d;border:1px solid #30363d;padding:5px 12px;border-radius:6px;font-size:12px">Salir</a></nav>
<div class="wrap"><a href="/servers" style="color:#8b949e;font-size:13px;display:inline-flex;align-items:center;gap:5px;margin-bottom:14px">&#8592; Servidores</a>
<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">{ic}<div><div style="font-size:19px;font-weight:700">{gname}</div><div style="font-size:12px;color:#8b949e">{len(channels)} canales - {len(roles)} roles</div></div></div>
<div class="tabs">
<button class="tab" data-tab="resumen" onclick="sw('resumen')">Resumen</button>
<button class="tab" data-tab="mensajes" onclick="sw('mensajes')">Mensajes</button>
<button class="tab" data-tab="miembros" onclick="sw('miembros')">Miembros</button>
<button class="tab" data-tab="moderacion" onclick="sw('moderacion')">Moderacion</button>
<button class="tab" data-tab="bienvenidas" onclick="sw('bienvenidas')">Bienvenidas</button>
<button class="tab" data-tab="purge" onclick="sw('purge')">Purge</button>
</div>
<div id="p-resumen" class="panel"><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px"><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px"><div style="font-size:26px;font-weight:700;color:#57f287">{len(channels)}</div><div style="font-size:11px;color:#8b949e">Canales</div></div><div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px"><div style="font-size:26px;font-weight:700;color:#58a6ff">{len(roles)}</div><div style="font-size:11px;color:#8b949e">Roles</div></div></div><div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:12px">Comandos slash de Discord</h3>{ch_html}</div></div>
<div id="p-mensajes" class="panel"><div id="ma" class="alert"></div><div id="ea" class="alert"></div>
<div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Enviar mensaje</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">El bot envia el mensaje al canal elegido.</p>
<div class="fg"><label>Canal</label><select id="mc"><option value="">Selecciona...</option>{copts}</select></div>
<div class="fg"><label>Mensaje</label><textarea id="mt" maxlength="2000" placeholder="Escribe aqui..."></textarea></div>
<button class="btn bg" onclick="sendMsg()">Enviar</button></div>
<div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Enviar embed</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">Mensaje con formato visual.</p>
<div class="fg"><label>Canal</label><select id="ec"><option value="">Selecciona...</option>{copts}</select></div>
<div class="fg"><label>Titulo</label><input type="text" id="et" placeholder="Titulo del embed"></div>
<div class="fg"><label>Descripcion</label><textarea id="ed" placeholder="Descripcion..."></textarea></div>
<div class="fg"><label>Color</label><input type="color" id="ecol" value="#57f287"></div>
<button class="btn bg" onclick="sendEmbed()">Enviar embed</button></div></div>
<div id="p-miembros" class="panel"><div id="mbal" class="alert"></div><div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Miembros</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">Envia DMs a cualquier miembro.</p><div id="mbl"><div style="color:#8b949e;font-size:13px;padding:20px;text-align:center">Cargando...</div></div></div></div>
<div id="p-moderacion" class="panel"><div id="modal" class="alert"></div><div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Moderacion</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">Ban, kick y timeout de miembros.</p><div id="moml"><div style="color:#8b949e;font-size:13px;padding:20px;text-align:center">Cargando...</div></div></div></div>
<div id="p-bienvenidas" class="panel"><div id="weal" class="alert"></div><div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Bienvenida</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">Usa {{user}} para mencionar al nuevo miembro.</p>
<div class="fg"><label>Canal</label><select id="wc"><option value="">Selecciona...</option>{copts}</select></div>
<div class="fg"><label>Mensaje en el canal</label><textarea id="wm" placeholder="Bienvenido {{user}}!"></textarea></div>
<div class="fg"><label>DM al nuevo miembro (opcional)</label><textarea id="wd" placeholder="Hola {{user}}!"></textarea></div>
<button class="btn bg" onclick="saveWelcome('{gid}')">Guardar</button></div></div>
<div id="p-purge" class="panel"><div id="pural" class="alert"></div><div class="card"><h3 style="font-size:15px;font-weight:600;margin-bottom:4px">Purge</h3><p style="font-size:12px;color:#8b949e;margin-bottom:14px">Elimina mensajes del canal (max 100).</p>
<div class="fg"><label>Canal</label><select id="pc"><option value="">Selecciona...</option>{copts}</select></div>
<div class="fg"><label>Cantidad</label><input type="number" id="pa" value="10" min="1" max="100"></div>
<button class="btn br" onclick="doPurge('{gid}')">Eliminar</button></div></div>
</div>
<script>
const GID="{gid}";
function show(id,msg,t){{const e=document.getElementById(id);e.textContent=msg;e.className='alert '+(t==='ok'?'as':'ae');e.style.display='block';setTimeout(()=>e.style.display='none',4000)}}
async function post(url,d){{const r=await fetch(url,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});return r.json()}}
function sw(n){{document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===n));document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='p-'+n))}}
async function sendMsg(){{const ch=document.getElementById('mc').value,ct=document.getElementById('mt').value;if(!ch||!ct)return show('ma','Selecciona canal y escribe mensaje','err');const r=await post('/api/msg',{{channel_id:ch,content:ct}});show('ma',r.ok?'Mensaje enviado!':'Error',r.ok?'ok':'err')}}
async function sendEmbed(){{const ch=document.getElementById('ec').value,title=document.getElementById('et').value,desc=document.getElementById('ed').value,color=parseInt(document.getElementById('ecol').value.replace('#',''),16);if(!ch)return show('ea','Selecciona canal','err');const r=await post('/api/embed',{{channel_id:ch,title,description:desc,color}});show('ea',r.ok?'Embed enviado!':'Error',r.ok?'ok':'err')}}
async function sendDm(uid,name){{const ct=document.getElementById('dm'+uid).value;if(!ct)return;const r=await post('/api/dm',{{user_id:uid,content:ct}});show('mbal',r.ok?'DM enviado a '+name:'Error',r.ok?'ok':'err');document.getElementById('dm'+uid).value=''}}
async function doBan(uid,name){{if(!confirm('Banear a '+name+'?'))return;const reason=prompt('Razon:','')||'Sin razon';const r=await post('/api/ban',{{guild_id:GID,user_id:uid,reason}});show('modal',r.ok?name+' baneado':'Error',r.ok?'ok':'err');if(r.ok)document.getElementById('mr'+uid)?.remove()}}
async function doKick(uid,name){{if(!confirm('Expulsar a '+name+'?'))return;const r=await post('/api/kick',{{guild_id:GID,user_id:uid}});show('modal',r.ok?name+' expulsado':'Error',r.ok?'ok':'err');if(r.ok)document.getElementById('mr'+uid)?.remove()}}
async function doTimeout(uid,name){{const m=prompt('Minutos para '+name+'?','10');if(!m)return;const r=await post('/api/timeout',{{guild_id:GID,user_id:uid,minutes:parseInt(m)}});show('modal',r.ok?name+' silenciado '+m+' min':'Error',r.ok?'ok':'err')}}
async function doPurge(gid){{const ch=document.getElementById('pc').value,am=document.getElementById('pa').value;if(!ch)return show('pural','Selecciona canal','err');const r=await post('/api/purge',{{channel_id:ch,amount:parseInt(am)}});show('pural',r.ok?r.deleted+' mensajes eliminados':'Error',r.ok?'ok':'err')}}
async function saveWelcome(gid){{const ch=document.getElementById('wc').value,msg=document.getElementById('wm').value,dm=document.getElementById('wd').value;const r=await post('/api/welcome',{{guild_id:gid,channel_id:ch,message:msg,dm_message:dm}});show('weal',r.ok?'Guardado!':'Error',r.ok?'ok':'err')}}
async function loadMembers(){{const r=await fetch('/api/members/'+GID);const ms=await r.json();let mb='',mo='';ms.forEach(m=>{{const u=m.user;if(u.bot)return;const nick=m.nick||u.global_name||u.username;const av=u.avatar?`<img src="https://cdn.discordapp.com/avatars/${{u.id}}/${{u.avatar}}.png" style="width:34px;height:34px;border-radius:50%">`:`<div style="width:34px;height:34px;border-radius:50%;background:#21262d;display:flex;align-items:center;justify-content:center;font-weight:700">${{u.username[0]}}</div>`;mb+=`<div class="mrow" id="mr${{u.id}}"><div>${{av}}</div><div style="flex:1;min-width:0;padding:0 4px"><div style="font-size:13px;font-weight:500">${{nick}}</div></div><button class="btn bb" style="padding:4px 8px;font-size:11px" onclick="let d=document.getElementById('da${{u.id}}');d.style.display=d.style.display==='none'?'flex':'none'">DM</button></div><div id="da${{u.id}}" style="display:none;padding:6px 0 10px;gap:6px;flex-wrap:wrap"><input type="text" id="dm${{u.id}}" placeholder="DM a ${{nick}}..." style="flex:1;min-width:140px"><button class="btn bb" style="font-size:11px;padding:5px 10px" onclick="sendDm('${{u.id}}','${{nick}}')">Enviar</button></div>`;
