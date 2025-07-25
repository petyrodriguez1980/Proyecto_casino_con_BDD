import sqlite3
import os
from datetime import datetime
import pytz
import uuid

DB_PATH = "casino.db"

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empleados (
                    id TEXT PRIMARY KEY,
                    nombre TEXT,
                    foto TEXT,
                    mesa TEXT,
                    mesa_asignada TEXT,
                    mensaje TEXT
                )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS finalizados (
                id TEXT PRIMARY KEY,
                nombre TEXT,
                foto TEXT,
                mesa TEXT,
                mesa_asignada TEXT,
                mensaje TEXT
            )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    accion TEXT,
                    destino TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

def agregar_empleado(empleado):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO empleados (id, nombre, foto, mesa, mesa_asignada, mensaje)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            empleado.get("id"),
            empleado.get("nombre"),
            empleado.get("foto", None),
            empleado.get("mesa", None),
            empleado.get("mesa_asignada", None),
            empleado.get("mensaje", "")
        ))
        conn.commit()

def obtener_empleados():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empleados")
        filas = cursor.fetchall()
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in filas]

def actualizar_empleado(empleado):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE empleados
            SET nombre = ?, foto = ?, mesa = ?, mesa_asignada = ?, mensaje = ?
            WHERE id = ?
        """, (
            empleado["nombre"], empleado["foto"], empleado["mesa"],
            empleado["mesa_asignada"], empleado["mensaje"], empleado["id"]
        ))
        conn.commit()

def mover_a_finalizados(empleado):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO finalizados (id, nombre) VALUES (?, ?)
        """, (empleado["id"], empleado["nombre"]))
        cursor.execute("DELETE FROM empleados WHERE id = ?", (empleado["id"],))
        conn.commit()

def obtener_finalizados():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finalizados")
        filas = cursor.fetchall()
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in filas]

def reingresar_empleado(emp):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM finalizados WHERE id = ?", (emp["id"],))
        cursor.execute("""
            INSERT INTO empleados (id, nombre, foto, mesa, mesa_asignada, mensaje)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            emp["id"],
            emp["nombre"],
            None,  # foto
            None if emp["mesa"] == "Sala de descanso" else emp["mesa"],
            None,  # mesa_asignada
            emp.get("mensaje", "")
        ))
        conn.commit()

def registrar_movimiento(nombre, accion, destino):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        zona_es = pytz.timezone("Europe/Madrid")
        ahora_local = datetime.now(zona_es)
        timestamp = ahora_local.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO movimientos (nombre, accion, destino, timestamp)
            VALUES (?, ?, ?, ?)
        """, (nombre, accion, destino, timestamp))
        conn.commit()

def obtener_movimientos():
    if not os.path.exists(DB_PATH):
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, accion, destino, timestamp
            FROM movimientos
            ORDER BY timestamp DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def obtener_empleados_en_mesa():
    empleados_en_mesa = {}

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Obtener todos los movimientos ordenados cronológicamente
        cursor.execute("SELECT * FROM movimientos ORDER BY timestamp ASC")
        movimientos = cursor.fetchall()

        for mov in movimientos:
            nombre = mov["nombre"]
            accion = mov["accion"]
            destino = mov["destino"]
            timestamp = datetime.strptime(mov["timestamp"], "%Y-%m-%d %H:%M:%S")

            # Buscar el ID del empleado actual
            cursor.execute("SELECT id FROM empleados WHERE nombre = ?", (nombre,))
            fila = cursor.fetchone()
            emp_id = fila["id"] if fila else str(uuid.uuid4())

            if accion == "Asignado":
                # Solo registrar si aún no está en mesa
                if nombre not in empleados_en_mesa:
                    empleados_en_mesa[nombre] = {
                        "id": emp_id,
                        "nombre": nombre,

                        "destino": destino,
                        "hora": timestamp
                    }
            elif accion in ["Liberado", "Finalizó"]:
                empleados_en_mesa.pop(nombre, None)

    return empleados_en_mesa

def mostrar_tiempo_en_mesa(emp):
    from streamlit.components.v1 import html
    from datetime import datetime

    nombre = emp["nombre"]

    destino = emp["destino"]
    hora = emp["hora"]  # datetime object

    epoch_ms = int(hora.timestamp() * 1000)

    reloj_html = f"""
    <div style='margin-bottom: 10px; font-weight: bold; color: darkgreen; font-size: 16px;'>
            {nombre} - {destino} -
            <span id="tiempo_{emp['id']}" style="text-decoration: underline;"></span>
    </div>
    <script>
        const inicio_{emp['id']} = {epoch_ms};
        function actualizar_{emp['id']}() {{
            const ahora = Date.now();
            let diff = Math.floor((ahora - inicio_{emp['id']}) / 1000);  // segundos

            const horas = String(Math.floor(diff / 3600)).padStart(2, '0');
            diff %= 3600;
            const minutos = String(Math.floor(diff / 60)).padStart(2, '0');
            const segundos = String(diff % 60).padStart(2, '0');

            document.getElementById("tiempo_{emp['id']}").textContent = `${{horas}}:${{minutos}}:${{segundos}}`;
        }}
        setInterval(actualizar_{emp['id']}, 1000);
        actualizar_{emp['id']}();
    </script>
    """
    html(reloj_html, height=35)