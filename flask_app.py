from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Caminho para o banco de dados simples (JSON)
DB_PATH = 'data/consoles.json'

def load_db():
    if not os.path.exists(DB_PATH):
        os.makedirs('data', exist_ok=True)
        with open(DB_PATH, 'w') as f:
            json.dump({"consoles": {}, "settings": {"version": "2.0.0 PRO", "status": "online", "nokv_enabled": True}}, f)
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- API PARA O CONSOLE (XBOX 360) ---

@app.route('/api/v1/auth', methods=['POST'])
def authenticate():
    data = request.json
    cpukey = data.get('cpukey')
    
    if not cpukey:
        return jsonify({"status": "error", "message": "CPUKey missing"}), 400
    
    db = load_db()
    
    # Auto-registro como usuário PRO GRATUITO por padrão
    if cpukey not in db['consoles']:
        db['consoles'][cpukey] = {
            "name": f"Console_{cpukey[:4]}",
            "added_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "type": "PRO", # Sempre PRO
            "nokv": True   # Sempre No KV
        }
        save_db(db)
    
    console = db['consoles'][cpukey]
    console['last_seen'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)
    
    return jsonify({
        "status": "success",
        "authorized": True,
        "mode": "PRO", # Força modo PRO
        "nokv_status": True, # Força No KV Ativo
        "server_version": db['settings']['version']
    })

@app.route('/api/v1/challenges', methods=['GET'])
def get_challenges():
    # Lógica de No KV: Envia hashes que simulam um KV limpo
    return jsonify({
        "challenge_id": secrets.token_hex(8),
        "kv_data": "NO_KV_ENCRYPTED_BLOB_FREE",
        "fcrt": True,
        "crl": False,
        "timestamp": datetime.now().timestamp()
    })

# --- PAINEL DE CONTROLE (ESTILO TETHERED ROXO) ---

@app.route('/')
def index():
    db = load_db()
    return render_template('dashboard.html', consoles=db['consoles'], settings=db['settings'])

@app.route('/admin/toggle_nokv')
def toggle_nokv():
    db = load_db()
    db['settings']['nokv_enabled'] = not db['settings']['nokv_enabled']
    save_db(db)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run()
