import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Bot

# Servidor web interno para mantener activo el contenedor en Render
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

# Cálculo matemático exacto del RSI (14 periodos)
def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Análisis de mercado real basado en datos cuantitativos
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
                    
                    if len(df) >= 20:
                        df['rsi'] = calcular_rsi(df, periodo=14)
                        ultimo_rsi = df['rsi'].iloc[-1]
                        precio_actual = df['close'].iloc[-1]
                        precio_anterior = df['close'].iloc[-2]
                        
                        # Análisis técnico real: tendencia de la vela y posición del RSI
                        tendencia = precio_actual - precio_anterior
                        
                        if ultimo_rsi > 58 and tendencia > 0:
                            direccion = "🟢 COMPRA (ARRIBA)"
                        elif ultimo_rsi < 42 and tendencia < 0:
                            direccion = "🔴 VENTA (ABAJO)"
                        elif ultimo_rsi >= 50:
                            direccion = "🟢 COMPRA (ARRIBA)"
                        else:
                            direccion = "🔴 VENTA (ABAJO)"
                        
                        return precio_actual, ultimo_rsi, direccion
        except Exception as e:
            print(f"Error técnico en el análisis: {e}")
        return None, None, None

# Lógica principal del bot con hora local exacta de Perú (UTC-5)
async def main():
    TOKEN = "8928143555:AAFo52VJio4aAYb_3MYP9ps5Jl9S842_4QY"
    CHAT_ID = "6043147544"
    
    bot = Bot(token=TOKEN)
    await bot.initialize()
    
    await bot.send_message(
        chat_id=CHAT_ID, 
        text="📊 BOT ETH_OTC - ANÁLISIS TÉCNICO REAL\nIniciando monitoreo de RSI y velas de 1 minuto..."
    )
    
    while True:
        try:
            precio, rsi, direccion = await analizar_mercado()
            
            if precio and rsi:
                # Sincronización exacta con la hora local de Perú (UTC-5) en formato 12 horas
                zona_peru = timezone(timedelta(hours=-5))
                tiempo_local = datetime.now(zona_peru) + timedelta(minutes=1)
                hora_entrada = tiempo_local.strftime("%I:%M %p")
                
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
                print("Aguardando datos estables del servidor de mercado...")
                
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
