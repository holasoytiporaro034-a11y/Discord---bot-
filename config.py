import os
import json

_BASE = os.path.dirname(os.path.abspath(__file__))

def _path(name):
    return os.path.join(_BASE, f"{name}_config.json")

def _load(name):
    p = _path(name)
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return {}

def _save(name, data):
    with open(_path(name), "w") as f:
        json.dump(data, f)

welcome_configs = _load("welcome")
verify_configs  = _load("verify")
logs_configs    = _load("logs")
ticket_configs  = _load("ticket")

def save_welcome(d): _save("welcome", d)
def save_verify(d):  _save("verify",  d)
def save_logs(d):    _save("logs",    d)
def save_ticket(d):  _save("ticket",  d)
