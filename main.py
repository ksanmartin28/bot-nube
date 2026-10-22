import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olymp Trade - Historial Real ETH_OTC</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background-color: #0b0e14; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #151c28; border: 1px solid #232d3f; border-radius: 16px; width: 100%; max-width: 520px; padding: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 1px solid #232d3f; padding-bottom: 16px; }
        .header h1 { color: #38bdf8; font-size: 22px; font-weight: 700; margin-bottom: 6px; }
        .badge { background: #0284c7; color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; font-weight: 600; }
        .btn-analizar { width: 100%; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border: none; padding: 16px; font-size: 16px; font-weight: 700; border-radius: 10px; cursor: pointer; transition: all 0.2s ease; }
        .btn-analizar:hover { background: linear-gradient(135deg, #1d4ed8, #1e40af); }
        
        .signal-box { margin-top: 20px; background: #0f172a; border-radius: 12px; padding: 18px; border: 1px solid #1e293b; display: none; }
        .signal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .pair-title { font-size: 17px; font-weight: 700; color: #f8fafc; }
        
        .operation { text-align: center; padding: 12px; border-radius: 8px; font-size: 18px; font-weight: 800; margin-bottom: 12px; }
        .buy { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid #22c55e; }
        .sell { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }
        
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px; margin-bottom: 12px; }
        .detail-item { background: #1e293b; padding: 8px 10px; border-radius: 6px; }
        .detail-item span { color: #94a3b8; display: block; font-size: 10px; margin-bottom: 2px; }
        .detail-item strong { color: #f1f5f9; font-size: 13px; }
        
        .verification-box { background: #111827; border-radius: 8px; padding: 10px; text-align: center; border: 1px dashed #374151; font-size: 13px; }
        .verifying { color: #facc15; font-weight: 600; }
        
        /* Historial */
        .history-section { margin-top: 24px; border-top: 1px solid #232d3f; padding-top: 16px; }
        .history-title { font-size: 15px; font-weight: 700; color: #38bdf8; margin-bottom: 10px; }
        .history-list { max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .history-item { background: #111827; padding: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; border-left: 4px solid #374151; }
        .history-item.win { border-left-color: #22c55e; }
        .history-item.loss { border-left-color: #ef4444; }
        
        .loading { text-align: center; color: #facc15; font-size: 14px; padding: 15px; font-style: italic; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Olymp Trade Signal AI</h1>
            <span class="badge">ETH_OTC - Análisis Real</span>
        </div>

        <button class="btn-analizar" onclick="obtenerSenalReal()">⚡ ANALIZAR Y GENERAR SEÑAL</button>

        <div id="loading" class="loading">
            Analizando el mercado real de ETH_OTC...
        </div>

        <div id="signal-box" class="signal-box">
            <div class="signal-header">
                <span class="pair-title">ETH_OTC</span>
                <span style="color: #94a3b8; font-size: 11px;">Duración: 1 MINUTO</span>
            </div>

            <div id="op-badge" class="operation buy">
                🟢 COMPRA (ARRIBA)
            </div>

            <div class="details-grid">
                <div class="detail-item">
                    <span>Entrada (Vela):</span>
                    <strong id="time-val">--:-- --</strong>
                </div>
                <div class="detail-item">
                    <span>Precio Apertura:</span>
                    <strong id="price-val">$0.00</strong>
                </div>
                <div class="detail-item">
                    <span>RSI (14):</span>
                    <strong id="rsi-val">0.0</strong>
                </div>
                <div class="detail-item">
                    <span>Estado:</span>
                    <strong id="status-text" style="color: #facc15;">Esperando inicio...</strong>
                </div>
            </div>

            <div class="verification-box">
                <div id="verifying-status" class="verifying">
                    ⏳ Esperando que inicie la vela de entrada...
                </div>
            </div>
        </div>

        <div class="history-section">
            <div class="history-title">📋 Historial de Operaciones</div>
            <div id="history-list" class="history-list">
                <div style="color: #64748b; text-align: center; font-size: 12px; padding: 10px;">Sin operaciones registradas aún.</div>
            </div>
        </div>
    </div>

    <script>
        async function obtenerSenalReal() {
            const loading = document.getElementById('loading');
            const signalBox = document.getElementById('signal-box');
            
            signalBox.style.display = 'none';
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
                    document.getElementById('status-text').innerText = 'En curso';

                    signalBox.style.display = 'block';

                    // Iniciar seguimiento exacto hasta el cierre de la vela
                    monitorearVela(data.precio_entrada, data.tipo_operacion, data.segundos_hasta_cierre, data.hora_entrada);
                } else {
                    alert('Error analizando el mercado. Intenta nuevamente.');
                }
            } catch (err) {
                loading.style.display = 'none';
                alert('Error de conexión con el servidor.');
            }
        }

        function monitorearVela(precioEntrada, tipoOperacion, segundosRestantes, horaEntrada) {
            const verifyingStatus = document.getElementById('verifying-status');
            let tiempoRestante = segundosRestantes + 60; // Incluye la vela actual completa + el minuto de la operación

            const timer = setInterval(() => {
                tiempoRestante--;
                
                if (tiempoRestante > 60) {
                    verifyingStatus.innerText = `⏳ Esperando apertura de vela (${tiempoRestante - 60}s)...`;
                } else if (tiempoRestante > 0) {
                    verifyingStatus.innerText = `⏳ Operación abierta. Cierra en: ${tiempoRestante}s`;
                } else {
                    clearInterval(timer);
                    verifyingStatus.innerText = `⌛ Validando precio de cierre oficial...`;
                    verificarResultadoFinal(precioEntrada, tipoOperacion, horaEntrada);
                }
            }, 1000);
        }

        async function verificarResultadoFinal(precioEntrada, tipoOperacion, horaEntrada) {
            try {
                const res = await fetch(`/api/verificar?precio_entrada=${precioEntrada}&tipo=${tipoOperacion}`);
                const data = await res.json();

                const verifyingStatus = document.getElementById('verifying-status');
                const statusText = document.getElementById('status-text');
                const historyList = document.getElementById('history-list');

                // Remover mensaje inicial si existe
                if (historyList.innerHTML.includes('Sin operaciones')) {
                    historyList.innerHTML = '';
                }

                const item = document.createElement('div');
                
                if (data.status === 'success') {
                    if (data.ganada) {
                        verifyingStatus.innerHTML = `<span style="color: #22c55e;">✅ ¡SEÑAL GANADA (ITM)! Cierre: $${data.precio_cierre}</span>`;
                        statusText.innerText = 'Ganada (ITM)';
                        statusText.style.color = '#22c55e';
                        item.className = 'history-item win';
                        item.innerHTML = `<span><b>${horaEntrada}</b> | ETH_OTC (${tipoOperacion})</span> <strong style="color: #22c55e;">WIN (+$${Math.abs(data.diferencia)})</strong>`;
                    } else {
                        verifyingStatus.innerHTML = `<span style="color: #ef4444;">❌ SEÑAL PERDIDA (OTM). Cierre: $${data.precio_cierre}</span>`;
                        statusText.innerText = 'Perdida (OTM)';
                        statusText.style.color = '#ef4444';
                        item.className = 'history-item loss';
                        item.innerHTML = `<span><b>${horaEntrada}</b> | ETH_OTC (${tipoOperacion})</span> <strong style="color: #ef4444;">LOSS (-$${Math.abs(data.diferencia)})</strong>`;
                    }
                } else {
                    verifyingStatus.innerHTML = `<span style="color: #ef4444;">Error al consultar el cierre.</span>`;
                }

                historyList.prepend(item);
            } catch (e) {
                console.error(e);
            }
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

async def consultar_datos_mercado():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
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
                            direccion, tipo_operacion = "🟢 COMPRA (ARRIBA)", "COMPRA"
                        elif ema_f < ema_s and rsi_val < 51:
                            direccion, tipo_operacion = "🔴 VENTA (ABAJO)", "VENTA"
                        else:
                            if precio_actual > df['close'].iloc[-2]:
                                direccion, tipo_operacion = "🟢 COMPRA (ARRIBA)", "COMPRA"
                            else:
                                direccion, tipo_operacion = "🔴 VENTA (ABAJO)", "VENTA"
                        
                        zona_peru = timezone(timedelta(hours=-5))
                        ahora = datetime.now(zona_peru)
                        
                        # Segundos exactos que faltan para que termine la vela actual y empiece la siguiente
                        segundos_hasta_inicio = 60 - ahora.second
                        
                        # Hora de la siguiente vela (la de entrada)
                        hora_entrada = (ahora + timedelta(seconds=segundos_hasta_inicio)).strftime("%I:%M %p")
                        
                        return {
                            "status": "success",
                            "precio_entrada": f"{precio_actual:.2f}",
                            "rsi": f"{rsi_val:.1f}",
                            "direccion": direccion,
                            "tipo_operacion": tipo_operacion,
                            "hora_entrada": hora_entrada,
                            "segundos_hasta_cierre": segundos_hasta_inicio
                        }
        except Exception as e:
            print(f"Error: {e}")
    return {"status": "error"}

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/analizar")
def api_analizar():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(consultar_datos_mercado())
    loop.close()
    return jsonify(res)

@app.route("/api/verificar")
def api_verificar():
    precio_entrada = float(request.args.get("precio_entrada", 0))
    tipo_operacion = request.args.get("tipo", "COMPRA")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(consultar_datos_mercado())
    loop.close()
    
    if res.get("status") == "success":
        precio_cierre = float(res["precio_entrada"])
        diferencia = round(abs(precio_cierre - precio_entrada), 2)
        
        if tipo_operacion == "COMPRA":
            ganada = precio_cierre > precio_entrada
        else:
            ganada = precio_cierre < precio_entrada
            
        return jsonify({
            "status": "success",
            "ganada": ganada,
            "precio_cierre": f"{precio_cierre:.2f}",
            "diferencia": f"{diferencia}"
        })
    
    return jsonify({"status": "error"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
