import os
import asyncio
import aiohttp
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Tus credenciales de Telegram
TELEGRAM_BOT_TOKEN = "8928143555:AAFo52VJio4aAYb_3MYP9ps5Jl9S842_4QY"
TELEGRAM_CHAT_ID = "6043147544"

async def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                await response.json()
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

async def analyze_market():
    print("[*] Bot en la nube iniciado...")
    await send_alert("☁️ *Bot en la nube conectado y operando 24/7.*")
    
    while True:
        try:
            # Monitoreo de precio de referencia (puedes cambiar la URL o la API según prefieras)
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT") as resp:
                    data = await resp.json()
                    price = float(data["price"])
                    print(f"[Monitoreo en nube] ETH Precio actual: {price}")
                    
            await asyncio.sleep(60) # Espera 60 segundos para el siguiente ciclo
        except Exception as e:
            print(f"Error en ciclo: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(analyze_market())