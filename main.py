import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
from telegram import Bot

# --- Servidor web interno para mantener el plan gratuito de Render activo ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Inicia el servidor de salud en segundo plano de forma automática
threading.Thread(target=run_health_check_server, daemon=True).start()

# --- Aquí va la lógica principal de tu bot de Telegram y Olymp Trade ---
async def main():
    # Token de tu bot y chat ID (asegúrate de tenerlos configurados en las variables de entorno de Render)
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")
    CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "TU_CHAT_ID_AQUI")
    
    bot = Bot(token=TOKEN)
    
    # Mensaje inicial para confirmar que conectó con éxito
    await bot.send_message(chat_id=CHAT_ID, text="☁️ Bot en la nube conectado y operando 24/7.")
    
    # Bucle principal para mantener el bot corriendo (aquí puedes integrar tu lógica de Olymp Trade ETH_OTC)
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
