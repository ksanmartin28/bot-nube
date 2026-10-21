import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Bot

# Servidor web interno para Render
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

# Función para calcular el RSI de 1 minuto
def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Función para obtener datos reales de ETH de 1 minuto
async def analizar_mercado():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data['chart']['result'][0]
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    closes = quotes['close']
                    
                    df = pd.DataFrame({'timestamp': timestamps, 'close': closes})
                    df = df.dropna().reset_index(drop=True)
                    df['close'] = df['close'].astype(float)
                    
                    if len(df) >= 15:
                        df['rsi'] = calcular_rsi(df, periodo=14)
                        ultimo_rsi = df['rsi'].iloc[-1]
                        precio_actual = df['close'].iloc[-1]
                        
                        # Lógica equilibrada para alternar señales de forma realista
                        # Si el RSI sube de 55 compra, si baja de 45 venta, zonas medias alternan por tendencia de cierre
                        cambio_precio = df['close'].diff().iloc[-1]
                        
                        if ultimo_rsi > 55 or (ultimo_rsi >= 50 and cambio_precio > 0):
                            direccion = "🟢 COMPRA (ARRIBA)"
                        elif ultimo_rsi < 45 or (ultimo_rsi < 50 and cambio_precio <= 0):
                            direccion = "🔴 VENTA (ABAJO)"
                        else:
                            direccion = "🟢 COMPRA (ARRIBA)" if cambio_precio > 0 else "🔴 VENTA (ABAJO)"
                        
                        return precio_actual, ultimo_rsi, direccion
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
        return None, None, None

# Lógica principal del bot
async def main():
    TOKEN = "8928143555:AAFo52VJio4aAYb_3MYP9ps5Jl9S842_4QY"
    CHAT_ID = "6043147544"
    
    bot = Bot(token=TOKEN)
    await bot.initialize()
    
    await bot.send_message(
        chat_id=CHAT_ID, 
        text="🚀 BOT ETH_OTC ACTUALIZADO\nSeñales dinámicas y hora en formato 12 horas..."
    )
    
    while True:
        try:
            precio, rsi, direccion = await analizar_mercado()
            
            if precio and rsi:
                # Hora de entrada calculada a 1 minuto en formato de 12 horas (Ej: 6:20 PM)
                tiempo_futuro = datetime.now() + timedelta(minutes=1)
                hora_entrada = tiempo_futuro.strftime("%I:%M %p")
                
                mensaje = (
                    "🚨 SEÑAL CONFIRMADA - ETH_OTC\n\n"
                    "📌 Par: ETH_OTC\n"
                    "⏱ Tiempo: 1 MINUTO\n"
                    f"🎯 Operación: {direccion}\n"
                    f"⏰ Hora de entrada: {hora_entrada}\n\n"
                    f"📊 Precio actual: {precio:.2f} | RSI (1m): {rsi:.1f}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=mensaje)
            else:
                print("Esperando datos del mercado...")
                
        except Exception as e:
            print(f"Error en el ciclo: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
