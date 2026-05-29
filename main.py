import asyncio, discord, os, threading, logging, requests as http
from discord import app_commands
from flask import Flask, redirect, request, session, jsonify
from functools import wraps
from datetime import datetime, timezone, timedelta
from html import escape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bot")

BOT_TOKEN=os.environ.get("DISCORD_TOKEN","")
CLIENT_ID=os.environ.get("DISCORD_CLIENT_ID","")
CLIENT_SECRET=os.environ.get("DISCORD_CLIENT_SECRET","")
SECRET_KEY=os.environ.get("SECRET_KEY","cambia-esta-clave")
BASE_URL=os.environ.get("BASE_URL","http://localhost:8080")
REDIRECT_URI=f"{BASE_URL}/callback"
API="https://discord.com/api/v10"

app=Flask(__name__)
app.secret_key=SECRET_KEY
welcome_configs={}

def bh(): return {"Authorization":f"Bot {BOT_TOKEN}"}
def uh(): return {"Authorization":f"Bearer {session.get('access_token','')}"}
def require_login(f):
    @wraps(f)
    def dec(*a,**kw):
        if "access_token" not in session: return redirect("/")
        return f(*a,**kw)
    return dec

@app.route('/')
def index():
    if 'access_token' in session: return redirect('/servers')
    return '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RANDOOM SUPPORT</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans
