import socketio
import subprocess
import time
import tkinter as tk
from tkinter import simpledialog
import platform
import sys

# --- CONFIGURATION ---
SERVER_URL = "botxxx-production.up.railway.app"  # Remplace par l'URL de ton serveur
DEVICE_NAME = platform.node()                # Nom de ton PC (ex: DESKTOP-XYZ)
# ---------------------

# Initialisation du client avec paramètres de reconnexion
sio = socketio.Client(reconnection=True, reconnection_delay=5)

def ask_permission(command):
    """Affiche une boîte de dialogue propre pour autoriser/refuser l'action."""
    try:
        root = tk.Tk()
        root.withdraw() # Cache la fenêtre principale, ne garde que la boîte de dialogue
        root.attributes("-topmost", True) # Force la fenêtre au premier plan
        
        prompt = (
            f"⚠️ UNE COMMANDE DISTANTE A ÉTÉ REÇUE ⚠️\n\n"
            f"Cible : {DEVICE_NAME}\n"
            f"Commande :\n{command}\n\n"
            f"Options de validation :\n"
            f"➔ 'y#' : Exécuter en tant que code Python\n"
            f"➔ 'yall' : Exécuter dans le terminal (OS)\n"
            f"➔ Laissez vide ou annulez pour refuser."
        )
        
        reponse = simpledialog.askstring("Autorisation requise", prompt, parent=root)
        root.destroy()
        
        return reponse.strip().lower() if reponse else 'n'
    except Exception as e:
        print(f"[!] Erreur d'interface graphique : {e}")
        return 'n' # Refus par défaut si la boîte de dialogue plante

@sio.event
def connect():
    print(f"[+] Connecté au serveur ! Enregistrement sous le nom : {DEVICE_NAME}")
    sio.emit('register_device', {'name': DEVICE_NAME})

@sio.event
def disconnect():
    print("[-] Déconnecté du serveur.")

@sio.on("new_command")
def on_message(data):
    command = data.get("cmd")
    if not command: 
        return

    print(f"\n[>] Nouvelle demande reçue : {command}")
    choix = ask_permission(command)

    if choix == 'n':
        print("[x] Action refusée par l'utilisateur.")
        return

    try:
        if choix == 'y#':
            print("[~] Exécution en tant que code Python...")
            exec(command)
            print("[✔] Code Python exécuté.")
            
        elif choix == 'yall':
            print("[~] Exécution dans le terminal OS...")
            # shell=True permet les commandes système (dir, ping, etc.)
            subprocess.Popen(command, shell=True) 
            print("[✔] Commande OS lancée en arrière-plan.")
        else:
            print("[x] Saisie invalide. Commande ignorée.")
            
    except Exception as e:
        print(f"[!] Erreur lors de l'exécution de la commande : {e}")

if __name__ == "__main__":
    print(f"[*] Démarrage du client d'écoute sur {DEVICE_NAME}...")
    
    while True:
        try:
            # Tente de se connecter si ce n'est pas déjà fait
            if not sio.connected:
                print(f"[*] Connexion à {SERVER_URL}...")
                sio.connect(SERVER_URL)
            
            # Bloque le script proprement pour écouter les événements
            sio.wait()
            
        except socketio.exceptions.ConnectionError:
            print("[-] Le serveur est injoignable. Nouvelle tentative dans 10 secondes...")
            time.sleep(10)
        except KeyboardInterrupt:
            # Permet de quitter proprement avec Ctrl+C
            print("\n[!] Arrêt manuel du client.")
            if sio.connected:
                sio.disconnect()
            break
        except Exception as e:
            print(f"[!] Erreur système inattendue : {e}")
            time.sleep(10)
