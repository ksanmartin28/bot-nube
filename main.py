import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Bot
from olymptrade_ws import OlympTradeClient  # Conexión basada en la estructura de la API de Olymp Trade

# Servidor web interno para mantener activo el plan gratuito de Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        return

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# Función para calcular el RSI
def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def main():
    # Credenciales de Telegram
    TOKEN = "8928143555:AAFo52VJio4aAYb_3MYP9ps5Jl9S842_4QY"
    CHAT_ID = "6043147544"
    
    bot = Bot(token=TOKEN)
    await bot.initialize()
    
    await bot.send_message(
        chat_id=CHAT_ID, 
        text="🚀 BOT OLYMP TRADE / ETH_OTC CONECTADO\nIniciando análisis de velas de 1 minuto..."
    )
    
    # Inicializar cliente de la API (requiere token de acceso si aplica en tu configuración)
    # Si estás usando entorno local o simulación con token:
    ACCESS_TOKEN = os.environ.get("OLYMP_TOKEN", "TU_TOKEN_AQUI")
    client = OlympTradeClient(access_token=ACCESS_TOKEN)
    
    try:
        await client.start()
        print("Conectado a la API correctamente.")
    except Exception as e:
        print(f"Error al iniciar cliente API: {e}")

    while True:
        try:
            # Obtener las últimas velas de 1 minuto (size=60) para ETH (o el par OTC correspondiente)
            candles = await client.market.get_candles("ETHUSD", size=60, count=30)
            
            if candles and len(candles) >= 15:
                df = pd.DataFrame(candles)
                df['close'] = df['close'].astype(float)
                
                df['rsi'] = calcular_rsi(df, periodo=14)
                ultimo_rsi = df['rsi'].iloc[-1]
                precio_actual = df['close'].iloc[-1]
                
                # Estrategia de cruce de RSI (50) para señales de 1 minuto
                if ultimo_rsi >= 50:
                    direccion = "🟢 COMPRA (ARRIBA)"
                else:
                    direccion = "🔴 VENTA (ABAJO)"
                
                hora_entrada = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M:00")
                
                mensaje = (
                    "🚨 SEÑAL CONFIRMADA - ETH_OTC\n\n"
                    "📌 Par: ETH_OTC\n"
                    "⏱ Tiempo: 1 MINUTO\n"
                    f"🎯 Operación: {direccion}\n"
                    f"⏰ Hora de entrada: {hora_entrada}\n\n"
                    f"📊 Precio actual: {precio_actual:.2f} | RSI (1m): {ultimo_rsi:.1f}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=mensaje)
            else:
                print("Esperando suficientes velas del mercado...")
                
        except Exception as e:
            print(f"Error en el ciclo de señales: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
