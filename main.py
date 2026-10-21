import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
from telegram import Bot

# Servidor web interno para mantener el plan gratuito de Render activo
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Inicia el servidor de salud en segundo plano automáticamente
threading.Thread(target=run_health_check_server, daemon=True).start()

# Lógica principal del bot
async def main():
    TOKEN = "7544078701:AAH66pZ_i1Y6wFkUeD7a9Nq8s2L3m4p5v6x"
    CHAT_ID = "6198083818"
    
    bot = Bot(token=TOKEN)
    
    # Mensaje inicial para confirmar la conexión
    await bot.send_message(chat_id=CHAT_ID, text="☁️ Bot en la nube conectado y operando 24/7.")
    
    # Bucle principal (aquí irá la lógica de tus señales de Olymp Trade ETH_OTC)
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
