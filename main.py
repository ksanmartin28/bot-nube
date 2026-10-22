import os
import asyncio
import pandas as pd
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olymp Trade - Panel Multi-Activo OTC</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background-color: #0b0e14; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #151c28; border: 1px solid #232d3f; border-radius: 16px; width: 100%; max-width: 520px; padding: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 1px solid #232d3f; padding-bottom: 16px; }
        .header h1 { color: #38bdf8; font-size: 22px; font-weight: 700; margin-bottom: 6px; }
        
        .asset-selector { margin-bottom: 15px; text-align: left; }
        .asset-selector label { display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-bottom: 6px; }
        .asset-selector select { width: 100%; background: #0f172a; color: #f8fafc; border: 1px solid #334155; padding: 10px 14px; border-radius: 8px; font-size: 14px; font-weight: 600; outline: none; cursor: pointer; }
        .asset-selector select:focus { border-color: #38bdf8; }

        .signal-box { background: #0f172a; border-radius: 12px; padding: 18px; border: 1px solid #1e293b; }
        .signal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .pair-title { font-size: 17px; font-weight: 700; color: #f8fafc; }
        
        .operation { text-align: center; padding: 14px; border-radius: 8px; font-size: 20px; font-weight: 800; margin-bottom: 12px; }
        .buy { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
        .sell { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
        .neutral { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid #475569; }
        
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px; margin-bottom: 12px; }
        .detail-item { background: #1e293b; padding: 8px 10px; border-radius: 6px; }
        .detail-item span { color: #94a3b8; display: block; font-size: 10px; margin-bottom: 2px; }
        .detail-item strong { color: #f1f5f9; font-size: 13px; }
        
        .verification-box { background: #111827; border-radius: 8px; padding: 12px; text-align: center; border: 1px dashed #374151; font-size: 13px; }
        .verifying { color: #facc15; font-weight: 600; }
        
        .history-section { margin-top: 24px; border-top: 1px solid #232d3f; padding-top: 16px; }
        .history-title { font-size: 15px; font-weight: 700; color: #38bdf8; margin-bottom: 10px; }
        .history-list { max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .history-item { background: #111827; padding: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; border-left: 4px solid #374151; }
        .history-item.win { border-left-color: #22c55e; }
        .history-item.loss { border-left-color: #ef4444; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Olymp Trade Signal AI</h1>
        </div>

        <div class="asset-selector">
            <label for="asset-select">Seleccionar Activo (Asset)</label>
            <select id="asset-select" onchange="cambiarActivo()">
                <option value="Ethereum OTC" selected>Ethereum OTC</option>
                <option value="EUR/USD (OTC)">EUR/USD (OTC)</option>
                <option value="USD/CAD (OTC)">USD/CAD (OTC)</option>
                <option value="GBP/USD (OTC)">GBP/USD (OTC)</option>
                <option value="USD/JPY (OTC)">USD/JPY (OTC)</option>
                <option value="Gold OTC">Gold OTC</option>
                <option value="Silver OTC">Silver OTC</option>
            </select>
        </div>

        <div class="signal-box">
            <div class="signal-header">
                <span id="active-pair-title" class="pair-title">Ethereum OTC</span>
                <span style="color: #94a3b8; font-size: 11px;">1 Minuto</span>
            </div>

            <div id="op-badge" class="operation neutral">
                ESPERANDO SEÑAL (FALTAN 5s)...
            </div>

            <div class="details-grid">
                <div class="detail-item">
                    <span>Próxima Entrada:</span>
                    <strong id="time-val">--:-- --</strong>
                </div>
                <div class="detail-item">
                    <span>Precio:</span>
                    <strong id="price-val">$0.00</strong>
                </div>
                <div class="detail-item">
                    <span>RSI (14):</span>
                    <strong id="rsi-val">0.0</strong>
                </div>
                <div class="detail-item">
                    <span>Estado:</span>
                    <strong id="status-text" style="color: #facc15;">Analizando...</strong>
                </div>
            </div>

            <div class="verification-box">
                <div id="verifying-status" class="verifying">
                    ⏳ Esperando el segundo :55 para ejecutar señal...
                </div>
            </div>
        </div>

        <div class="history-section">
            <div class="history-title">📋 Historial de Operaciones</div>
            <div id="history-list" class="history-list">
                <div style="color: #64748b; text-align: center; font-size: 12px; padding: 10px;">Esperando cierres de velas...</div>
            </div>
        </div>
    </div>

    <script>
        let ultimoMinutoProcesado = null;
        let operacionActiva = null;

        function cambiarActivo() {
            const select = document.getElementById('asset-select');
            document.getElementById('active-pair-title').innerText = select.value;
            ultimoMinutoProcesado = null;
            operacionActiva = null;
            document.getElementById('history-list').innerHTML = '<div style="color: #64748b; text-align: center; font-size: 12px; padding: 10px;">Cambiado de activo. Esperando ciclos...</div>';
        }

        async function cicloEnVivo() {
            try {
                const asset = document.getElementById('asset-select').value;
                const res = await fetch(`/api/analizar?asset=${encodeURIComponent(asset)}`);
                const data = await res.json();

                if (data.status === 'success') {
                    const segundosRestantes = data.segundos_restantes;
                    const minutoActual = data.minuto_actual;

                    document.getElementById('price-val').innerText = '$' + data.precio_actual;
                    document.getElementById('rsi-val').innerText = data.rsi;
                    document.getElementById('time-val').innerText = data.hora_siguiente;

                    const opBadge = document.getElementById('op-badge');
                    const statusText = document.getElementById('status-text');
                    const verifyingStatus = document.getElementById('verifying-status');

                    if (segundosRestantes <= 5 && segundosRestantes >= 0) {
                        if (ultimoMinutoProcesado !== minutoActual + asset) {
                            ultimoMinutoProcesado = minutoActual + asset;

                            if (data.direccion.includes('COMPRA')) {
                                opBadge.className = 'operation buy';
                                opBadge.innerText = '🟢 COMPRA (ARRIBA)';
                            } else {
                                opBadge.className = 'operation sell';
                                opBadge.innerText = '🔴 VENTA (ABAJO)';
                            }

                            statusText.innerText = 'Confirmada';
                            statusText.style.color = '#22c55e';
                            verifyingStatus.innerHTML = `<b style="color: #4ade80;">¡ENTRADA A LAS ${data.hora_siguiente}!</b>`;

                            operacionActiva = {
                                asset: asset,
                                precioApertura: parseFloat(data.precio_actual),
                                tipo: data.tipo_operacion,
                                hora: data.hora_siguiente
                            };
                        }
                    } else if (segundosRestantes > 5 && segundosRestantes < 55) {
                        if (operacionActiva && operacionActiva.hora === data.hora_actual_formato) {
                            statusText.innerText = 'En curso';
                            statusText.style.color = '#facc15';
                            verifyingStatus.innerText = `⏳ Operación abierta. Cierra en ${segundosRestantes}s.`;
                        } else {
                            opBadge.className = 'operation neutral';
                            opBadge.innerText = 'ESPERANDO SEÑAL (FALTAN 5s)...';
                            statusText.innerText = 'Escaneando';
                            statusText.style.color = '#facc15';
                            verifyingStatus.innerText = `⏳ Monitoreando ${asset}... (${segundosRestantes - 5}s)`;
                        }
                    }

                    if (operacionActiva && operacionActiva.hora !== data.hora_actual_formato && segundosRestantes >= 55) {
                        validarResultadoFinal(operacionActiva.asset, operacionActiva.precioApertura, parseFloat(data.precio_actual), operacionActiva.tipo, operacionActiva.hora);
                        operacionActiva = null;
                    }
                }
            } catch (err) {
                console.error("Error:", err);
            }
        }

        async function validarResultadoFinal(asset, precioApertura, precioCierre, tipoOperacion, horaEntrada) {
            try {
                const res = await fetch(`/api/verificar?precio_apertura=${precioApertura}&precio_cierre=${precioCierre}&tipo=${tipoOperacion}`);
                const data = await res.json();

                const historyList = document.getElementById('history-list');
                if (historyList.innerHTML.includes('Esperando') || historyList.innerHTML.includes('Cambiado')) {
                    historyList.innerHTML = '';
                }

                const item = document.createElement('div');
                if (data.ganada) {
                    item.className = 'history-item win';
                    item.innerHTML = `<span><b>${horaEntrada}</b> | ${asset} (${tipoOperacion})</span> <strong style="color: #22c55e;">WIN (+${data.diferencia})</strong>`;
                } else {
                    item.className = 'history-item loss';
                    item.innerHTML = `<span><b>${horaEntrada}</b> | ${asset} (${tipoOperacion})</span> <strong style="color: #ef4444;">LOSS (-${data.diferencia})</strong>`;
                }
                historyList.prepend(item);
            } catch (e) {
                console.error("Error al validar:", e);
            }
        }

        setInterval(cicloEnVivo, 1000);
    </script>
</body>
</html>
"""

historial_activos = {
    "Ethereum OTC": [2422.10 + (i * 0.02) for i in range(50)],
    "EUR/USD (OTC)": [1.0850 + (i * 0.0001) for i in range(50)],
    "USD/CAD (OTC)": [1.3620 + (i * 0.0001) for i in range(50)],
    "GBP/USD (OTC)": [1.2750 + (i * 0.0001) for i in range(50)],
    "USD/JPY (OTC)": [155.20 + (i * 0.01) for i in range(50)],
    "Gold OTC": [2330.50 + (i * 0.05) for i in range(50)],
    "Silver OTC": [28.40 + (i * 0.005) for i in range(50)]
}

def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    return 100 - (100 / (1 + rs))

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/analizar")
def api_analizar():
    asset = request.args.get("asset", "Ethereum OTC")
    if asset not in historial_activos:
        asset = "Ethereum OTC"
        
    ticks = historial_activos[asset]
    ultimo = ticks[-1]
    
    if "JPY" in asset:
        variacion = random.uniform(-0.04, 0.04)
        dec = 2
    elif "Gold" in asset:
        variacion = random.uniform(-0.15, 0.15)
        dec = 2
    elif "Ethereum" in asset:
        variacion = random.uniform(-0.06, 0.06)
        dec = 4
    else:
        variacion = random.uniform(-0.0004, 0.0004)
        dec = 4

    precio_actual = round(ultimo + variacion, dec)
    
    ticks.append(precio_actual)
    if len(ticks) > 60:
        ticks.pop(0)

    df = pd.DataFrame({'close': ticks})
    df['close'] = df['close'].astype(float)
    df['rsi'] = calcular_rsi(df, 14)
    df['ema_fast'] = df['close'].ewm(span=3, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=8, adjust=False).mean()
    
    rsi_val = df['rsi'].iloc[-1]
    ema_f = df['ema_fast'].iloc[-1]
    ema_s = df['ema_slow'].iloc[-1]
    impulso = precio_actual - df['close'].iloc[-2]
    
    if ema_f > ema_s and rsi_val >= 48 and rsi_val <= 70 and impulso >= 0:
        direccion, tipo_operacion = "🟢 COMPRA (ARRIBA)", "COMPRA"
    elif ema_f < ema_s and rsi_val <= 52 and rsi_val >= 30 and impulso <= 0:
        direccion, tipo_operacion = "🔴 VENTA (ABAJO)", "VENTA"
    else:
        if rsi_val < 32:
            direccion, tipo_operacion = "🟢 COMPRA (ARRIBA)", "COMPRA"
        elif rsi_val > 68:
            direccion, tipo_operacion = "🔴 VENTA (ABAJO)", "VENTA"
        else:
            if impulso > 0:
                direccion, tipo_operacion = "🟢 COMPRA (ARRIBA)", "COMPRA"
            else:
                direccion, tipo_operacion = "🔴 VENTA (ABAJO)", "VENTA"
        
    zona_peru = timezone(timedelta(hours=-5))
    ahora = datetime.now(zona_peru)
    segundos_restantes = 60 - ahora.second
    
    minuto_actual = ahora.strftime("%Y-%m-%d %H:%M")
    hora_actual_formato = ahora.strftime("%I:%M %p")
    siguiente_tiempo = ahora + timedelta(seconds=segundos_restantes)
    hora_siguiente = siguiente_tiempo.strftime("%I:%M %p")
    
    return jsonify({
        "status": "success",
        "precio_actual": f"{precio_actual:.{dec}f}",
        "rsi": f"{rsi_val:.1f}",
        "direccion": direccion,
        "tipo_operacion": tipo_operacion,
        "segundos_restantes": segundos_restantes,
        "minuto_actual": minuto_actual,
        "hora_actual_formato": hora_actual_formato,
        "hora_siguiente": hora_siguiente
    })

@app.route("/api/verificar")
def api_verificar():
    precio_apertura = float(request.args.get("precio_apertura", 0))
    precio_cierre = float(request.args.get("precio_cierre", 0))
    tipo_operacion = request.args.get("tipo", "COMPRA")
    
    diferencia = round(abs(precio_cierre - precio_apertura), 4)
    
    if tipo_operacion == "COMPRA":
        ganada = precio_cierre > precio_apertura
    else:
        ganada = precio_cierre < precio_apertura
        
    return jsonify({
        "status": "success",
        "ganada": ganada,
        "diferencia": f"{diferencia}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
