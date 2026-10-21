import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
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

# Inicia el servidor de salud en segundo plano
threading.Thread(target=run_health_check_server, daemon=True).start()

# Función para calcular el RSI de 1 minuto
def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Función para obtener datos reales de Binance (ETH/USDT) en tiempo real
async def analizar_mercado():
    url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1m&limit=30"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                
                # Cálculo del RSI de 1 minuto
                df['rsi'] = calcular_rsi(df, periodo=14)
                ultimo_rsi = df['rsi'].iloc[-1]
                precio_actual = df['close'].iloc[-1]
                
                # Estrategia de 1 minuto en tiempo real (Cruce del nivel 50 del RSI)
                if ultimo_rsi >= 50:
                    direccion = "🟢 COMPRA (ARRIBA)"
                else:
                    direccion = "🔴 VENTA (ABAJO)"
                
                return precio_actual, ultimo_rsi, direccion
            return None, None, None

# Lógica principal del bot
async def main():
    TOKEN = "8928143555:AAFo52VJio4aAYb_3MYP9ps5Jl9S842_4QY"
    CHAT_ID = "6043147544"
    
    bot = Bot(token=TOKEN)
    
    await bot.send_message(
        chat_id=CHAT_ID, 
        text="🚀 BOT ETH_OTC ACTIVADO\nEnviando señales reales en tiempo real cada 1 minuto..."
    )
    
    while True:
        try:
            precio, rsi, direccion = await analizar_mercado()
            
            if precio and rsi:
                # Hora exacta para la siguiente vela de 1 minuto
                hora_entrada = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M:00")
                
                mensaje = (
                    "🚨 SEÑAL CONFIRMADA - ETH_OTC\n\n"
                    "📌 Par: ETH_OTC\n"
                    "⏱ Tiempo: 1 MINUTO\n"
                    f"🎯 Operación: {direccion}\n"
                    f"⏰ Hora de entrada: {hora_entrada}\n\n"
                    f"📊 Precio actual: {precio:.2f} | RSI (1m): {rsi:.1f}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=mensaje)
                
        except Exception as e:
            print(f"Error en el análisis: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
