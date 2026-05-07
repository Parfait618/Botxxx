const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const devices = new Map();
const API_KEY = process.env.API_KEY || "mdp"; 

io.on('connection', (socket) => {
    socket.on('register_device', (data) => {
        if (!data?.name) return;
        devices.set(data.name, socket.id);
        socket.deviceName = data.name; 
        console.log(`[✔] ${data.name} est en ligne.`);
    });

    socket.on('disconnect', () => {
        if (socket.deviceName) {
            devices.delete(socket.deviceName);
            console.log(`[-] ${socket.deviceName} est hors ligne.`);
        }
    });
});

app.get('/send', async (req, res) => {
    const { to, cmd, key } = req.query;

    if (key !== API_KEY) return res.status(401).json({ error: "Clé API invalide" });
    if (!to || !cmd) return res.status(400).json({ error: "Paramètres manquants" });

    const targetSocketId = devices.get(to);
    if (!targetSocketId) return res.status(404).json({ error: "Appareil hors ligne" });

    console.log(`[>] Envoi à ${to} : ${cmd}`);

    // --- LE CŒUR DE L'AMÉLIORATION ---
    // On utilise une promesse pour attendre la réponse du client Python
    try {
        const response = await new Promise((resolve, reject) => {
            // On envoie la commande avec un callback (timeout de 60s)
            const timer = setTimeout(() => reject("Timeout : Pas de réponse de l'utilisateur"), 60000);

            io.to(targetSocketId).timeout(55000).emit('new_command', { cmd }, (err, replies) => {
                clearTimeout(timer);
                if (err) reject("L'appareil n'a pas répondu à temps.");
                else resolve(replies[0]); // On récupère la réponse (y#, yall, n)
            });
        });

        res.status(200).json({ success: true, device_response: response });
    } catch (error) {
        res.status(504).json({ success: false, error: error });
    }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`🚀 Serveur sur port ${PORT} | Key: ${API_KEY}`));
