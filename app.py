"""Registro concurrente con Flask y Astra DB por HTTPS (Data API)."""

import os
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from astrapy import DataAPIClient
from dotenv import load_dotenv
from flask import Flask, render_template_string, request

load_dotenv()
app = Flask(__name__)

PAGINA = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Registro concurrente · Cassandra</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; display: grid; place-items: center;
               font-family: system-ui, Arial, sans-serif; background: #f1f5f9; color: #172033; }
        main { width: min(420px, 92vw); padding: 32px; background: white;
               border: 1px solid #e2e8f0; border-radius: 18px;
               box-shadow: 0 12px 38px #17203314; }
        .eyebrow { color: #3461c2; font-size: 12px; font-weight: 700;
                   letter-spacing: .09em; text-transform: uppercase; }
        h1 { font-size: 26px; margin: 12px 0 8px; }
        p { color: #64748b; line-height: 1.5; }
        label { display: block; font-weight: 600; margin: 25px 0 8px; }
        input { width: 100%; padding: 13px 14px; border: 1px solid #cbd5e1;
                border-radius: 9px; font: inherit; }
        input:focus { outline: 2px solid #93c5fd; border-color: #2563eb; }
        button { width: 100%; margin-top: 15px; padding: 14px; border: 0;
                 border-radius: 9px; background: #2563eb; color: white;
                 font: inherit; font-weight: 700; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        .aviso { padding: 13px; border-radius: 9px; margin-top: 18px; font-size: 14px; }
        .ok { background: #ecfdf5; color: #065f46; }
        .error { background: #fef2f2; color: #991b1b; }
        footer { margin-top: 22px; color: #94a3b8; font-size: 12px; }
    </style>
</head>
<body>
    <main>
        <div class="eyebrow">Base de Datos III · Práctica 1</div>
        <h1>Registro concurrente</h1>
        <p>Escribe tu nombre y envíalo. Se guardará directamente en Cassandra en la nube.</p>
        <form method="post">
            <label for="nombre">Tu nombre</label>
            <input id="nombre" name="nombre" type="text" maxlength="80"
                   placeholder="Ejemplo: María" required autofocus>
            <button type="submit">Enviar registro</button>
        </form>
        {% if mensaje %}
            <div class="aviso {{ 'ok' if correcto else 'error' }}" role="status">{{ mensaje }}</div>
        {% endif %}
        <footer>Apache Cassandra · Astra DB · Flask</footer>
    </main>
</body>
</html>
"""


@lru_cache(maxsize=1)
def obtener_tabla():
    """Prepara el cliente de Astra una vez por proceso; usa HTTPS/443."""
    endpoint = os.environ["ASTRA_API_ENDPOINT"].strip()
    token = os.environ["ASTRA_TOKEN"].strip()
    keyspace = os.getenv("ASTRA_KEYSPACE", "universidad").strip()
    cliente = DataAPIClient()
    bd = cliente.get_database(endpoint, token=token, keyspace=keyspace)
    return bd.get_table("usuarios")


@app.route("/", methods=["GET", "POST"])
def inicio():
    if request.method == "GET":
        return render_template_string(PAGINA, mensaje=None, correcto=False)

    nombre = request.form.get("nombre", "").strip()
    if not nombre or len(nombre) > 80:
        return render_template_string(
            PAGINA, mensaje="Escribe un nombre de 1 a 80 caracteres.", correcto=False
        ), 400

    try:
        tabla = obtener_tabla()
        inicio_escritura = time.perf_counter()
        tabla.insert_one({
            "id": uuid.uuid4(),
            "nombre": nombre,
            "fecha": datetime.now(timezone.utc),
        })
        milisegundos = (time.perf_counter() - inicio_escritura) * 1000
        return render_template_string(
            PAGINA,
            mensaje=f"¡{nombre}, registro guardado en Cassandra! Escritura: {milisegundos:.1f} ms.",
            correcto=True,
        )
    except Exception:
        app.logger.exception("No se pudo registrar al participante en Astra DB")
        return render_template_string(
            PAGINA,
            mensaje="No se pudo guardar. Revisa ASTRA_API_ENDPOINT, ASTRA_TOKEN y la tabla universidad.usuarios.",
            correcto=False,
        ), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False, threaded=True)
