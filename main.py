import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Plantilla HTML/JS responsiva y moderna en modo oscuro
HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olymp Trade - Panel Real ETH_OTC</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background-color: #0b0e14; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #151c28; border: 1px solid #232d3f; border-radius: 16px; width: 100%; max-width: 480px; padding: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 1px solid #232d3f; padding-bottom: 16px; }
        .header h1 { color: #38bdf8; font-size: 22px; font-weight: 700; margin-bottom: 6px; }
        .badge { background: #0284c7; color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
        .btn-analizar { width: 100%; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border: none; padding: 16px; font-size: 16px; font-weight: 700; border-radius: 10px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
        .btn-analizar:hover { background: linear-gradient(135deg, #1d4ed8, #1e40af); transform: translateY(-1px); }
        .btn-analizar:active { transform: translateY(1px); }
        .btn-analizar:disabled { background: #334155; cursor: not-allowed; box-shadow: none; }
        
        .signal-box { margin-top: 24px; background: #0f172a; border-radius: 12px; padding: 20px; border: 1px solid #1e293b; display: none; }
        .signal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .pair-title { font-size: 18px; font-weight: 700; color: #f8fafc; }
        
        .operation { text-align: center; padding: 14px; border-radius: 8px; font-size: 20px; font-weight: 800; margin-bottom: 16px; letter-spacing: 0.5px; }
        .buy { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid #22c55e; }
        .sell { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }
        
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px; margin-bottom: 16px; }
        .detail-item { background: #1e293b; padding: 10px 12px; border-radius: 6px; }
        .detail-item span { color: #94a3b8; display: block; font-size: 11px; margin-bottom: 2px; }
        .detail-item strong { color: #f1f5f9; font-size: 14px; }
        
        /* Caja de Verificación de Resultado */
        .verification-box { background: #111827; border-radius: 8px; padding: 14px; text-align: center; border: 1px dashed #374151; }
        .verifying { color: #facc15; font-weight: 600; font-size: 13px; animation: pulse 1.5s infinite; }
        .result-win { color: #22c55e; font-size: 16px; font-weight: 800; }
        .result-loss { color: #ef4444; font-size: 16px; font-weight: 800; }
        
        .loading { text-align: center; color: #facc15; font-size: 14px; padding: 20px; font-style: italic; display: none; }

        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Olymp Trade Signal AI</h1>
            <span class="badge">Mercado Real ETH_OTC</span>
        </div>

        <button id="btn-main" class="btn-analizar" onclick="obtenerSenalReal()">⚡ ANALIZAR Y GENERAR SEÑAL</button>

        <div id="loading" class="loading">
            Conectando con servidores y analizando RSI/EMAs en tiempo real...
        </div>

        <div id="signal-box" class="signal-box">
            <div class="signal-header">
                <span class="pair-title">ETH_OTC</span>
                <span style="color: #94a3b8; font-size: 12px;">Tiempo: 1 MIN</span>
            </div>

            <div id="op-badge" class="operation buy">
                🟢 COMPRA (ARRIBA)
            </div>

            <div class="details-grid">
                <div class="detail-item">
                    <span>Hora de Entrada:</span>
                    <strong id="time-val">--:-- --</strong>
                </div>
                <div class="detail-item">
                    <span>Precio de Entrada:</span>
                    <strong id="price-val">$0.00</strong>
                </div>
                <div class="detail-item">
                    <span>RSI (14):</span>
                    <strong id="rsi-val">0.0</strong>
                </div>
                <div class="detail-item">
                    <span>Fuente:</span>
                    <strong style="color: #38bdf8;">Mercado Real EN VIVO</strong>
                </div>
            </div>

            <div class="verification-box">
                <div id="verifying-status" class="verifying">
                    ⏳ Esperando fin de vela (60s) para verificar resultado real...
                </div>
                <div id="result-status" style="display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        let countdownTimer = null;

        async function obtenerSenalReal() {
            const btn = document.getElementById('btn-main');
            const loading = document.getElementById('loading');
            const signalBox = document.getElementById('signal-box');
            const verifyingStatus = document.getElementById('verifying-status');
            const resultStatus = document.getElementById('result-status');

            btn.disabled = true;
            signalBox.style.display = 'none';
            resultStatus.style.display = 'none';
            loading.style.display = 'block';

            try {
                const res = await fetch('/api/analizar');
                const data = await res.json();

                loading.style.display = 'none';

                if (data.status === 'success') {
                    const opBadge = document.getElementById('op-badge');
                    if (data.direccion.includes('COMPRA')) {
                        opBadge.className = 'operation buy';
                        opBadge.innerText = '🟢 COMPRA (ARRIBA)';
                    } else {
                        opBadge.className = 'operation sell';
                        opBadge.innerText = '🔴 VENTA (ABAJO)';
                    }

                    document.getElementById('time-val').innerText = data.hora_entrada;
                    document.getElementById('price-val').innerText = '$' + data.precio_entrada;
                    document.getElementById('rsi-val').innerText = data.rsi;

                    verifyingStatus.style.display = 'block';
                    signalBox.style.display = 'block';

                    // Iniciar cuenta regresiva para verificar el resultado exacto tras 60 segundos
                    iniciarVerificacion(data.precio_entrada, data.tipo_operacion);
                } else {
                    alert('Error extrayendo cotizaciones. Intenta nuevamente.');
                    btn.disabled = false;
                }
            } catch (err) {
                loading.style.display = 'none';
                btn.disabled = false;
                alert('Error de red al consultar el servidor.');
            }
        }

        function iniciarVerificacion(precioEntrada, tipoOperacion) {
            let segundosRestantes = 60;
            const verifyingStatus = document.getElementById('verifying-status');
            const resultStatus = document.getElementById('result-status');
            const btn = document.getElementById('btn-main');

            if (countdownTimer) clearInterval(countdownTimer);

            countdownTimer = setInterval(() => {
                segundosRestantes--;
                verifyingStatus.innerText = `⏳ Verificando resultado real en: ${segundosRestantes}s...`;

                if (segundosRestantes <= 0) {
                    clearInterval(countdownTimer);
                    verifyingStatus.style.display = 'none';
                    verificandoResultadoReal(precioEntrada, tipoOperacion);
                }
            }, 1000);
        }

        async function verificandoResultadoReal(precioEntrada, tipoOperacion) {
            const resultStatus = document.getElementById('result-status');
            const btn = document.getElementById('btn-main');

            resultStatus.style.display = 'block';
            resultStatus.className = 'verifying';
            resultStatus.innerText = 'Obteniendo precio de cierre real...';

            try {
                const res = await fetch(`/api/verificar?precio_entrada=${precioEntrada}&tipo=${tipoOperacion}`);
                const data = await res.json();

                if (data.status === 'success') {
                    if (data.ganada) {
                        resultStatus.className = 'result-win';
                        resultStatus.innerHTML = `✅ ¡SEÑAL GANADA! (ITM)<br><span style="font-size: 12px; color: #94a3b8;">Precio Cierre: $${data.precio_cierre} (Diferencia: ${data.diferencia})</span>`;
                    } else {
                        resultStatus.className = 'result-loss';
                        resultStatus.innerHTML = `❌ SEÑAL PERDIDA (OTM)<br><span style="font-size: 12px; color: #94a3b8;">Precio Cierre: $${data.precio_cierre} (Diferencia: ${data.diferencia})</span>`;
                    }
                } else {
                    resultStatus.innerHTML = '<span style="color: #ef4444;">Error al obtener el precio de cierre.</span>';
                }
            } catch (e) {
                resultStatus.innerHTML = '<span style="color: #ef4444;">Error al validar resultado.</span>';
            }

            btn.disabled = false;
        }
    </script>
</body>
</html>
"""

def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    return 100 - (100 / (1 + rs))

async def obtener_datos_mercado():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data['chart']['result'][0]
                    closes = result['indicators']['quote'][0]['close']
                    
                    df = pd.DataFrame({'close': closes}).dropna().reset_index(drop=True)
                    df['close'] = df['close'].astype(float)
                    
                    if len(df) >= 20:
                        df['rsi'] = calcular_rsi(df, 14)
                        df['ema_fast'] = df['close'].ewm(span=3, adjust=False).mean()
                        df['ema_slow'] = df['close'].ewm(span=8, adjust=False).mean()
                        
                        rsi_val = df['rsi'].iloc[-1]
                        precio_actual = df['close'].iloc[-1]
                        ema_f = df['ema_fast'].iloc[-1]
                        ema_s = df['ema_slow'].iloc[-1]
                        
                        if ema_f > ema_s and rsi_val >= 49:
                            direccion = "🟢 COMPRA (ARRIBA)"
                            tipo_operacion = "COMPRA"
                        elif ema_f < ema_s and rsi_val < 51:
                            direccion = "🔴 VENTA (ABAJO)"
                            tipo_operacion = "VENTA"
                        else:
                            if precio_actual > df['close'].iloc[-2]:
                                direccion = "🟢 COMPRA (ARRIBA)"
                                tipo_operacion = "COMPRA"
                            else:
                                direccion = "🔴 VENTA (ABAJO)"
                                tipo_operacion = "VENTA"
                        
                        zona_peru = timezone(timedelta(hours=-5))
                        hora_entrada = (datetime.now(zona_peru) + timedelta(minutes=1)).strftime("%I:%M %p")
                        
                        return {
                            "status": "success",
                            "precio_entrada": f"{precio_actual:.2f}",
                            "rsi": f"{rsi_val:.1f}",
                            "direccion": direccion,
                            "tipo_operacion": tipo_operacion,
                            "hora_entrada": hora_entrada
                        }
        except Exception as e:
            print(f"Error procesando datos: {e}")
    return {"status": "error"}

async def obtener_precio_cierre_real():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
                    closes_clean = [float(c) for c in closes if c is not None]
                    return closes_clean[-1]
        except Exception as e:
            print(f"Error precio cierre: {e}")
    return None

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/analizar")
def api_analizar():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(obtener_datos_mercado())
    loop.close()
    return jsonify(res)

@app.route("/api/verificar")
def api_verificar():
    precio_entrada = float(request.args.get("precio_entrada", 0))
    tipo_operacion = request.args.get("tipo", "COMPRA")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    precio_cierre = loop.run_until_complete(obtener_precio_cierre_real())
    loop.close()
    
    if precio_cierre is not None:
        diferencia = round(precio_cierre - precio_entrada, 2)
        if tipo_operacion == "COMPRA":
            ganada = precio_cierre > precio_entrada
        else:
            ganada = precio_cierre < precio_entrada
            
        return jsonify({
            "status": "success",
            "ganada": ganada,
            "precio_cierre": f"{precio_cierre:.2f}",
            "diferencia": f"{diferencia:+.2f}"
        })
    
    return jsonify({"status": "error"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
