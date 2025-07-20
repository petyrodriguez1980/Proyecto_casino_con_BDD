import sqlite3
import os
from datetime import datetime
import pytz

DB_PATH = "casino.db"

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empleados (
                    id TEXT PRIMARY KEY,
                    nombre TEXT,
                    categoria TEXT,
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
                    categoria TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    categoria TEXT,
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
            INSERT INTO empleados (id, nombre, categoria, foto, mesa, mesa_asignada, mensaje)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            empleado["id"], empleado["nombre"], empleado["categoria"], empleado["foto"],
            empleado["mesa"], empleado["mesa_asignada"], empleado["mensaje"]
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
            SET nombre = ?, categoria = ?, foto = ?, mesa = ?, mesa_asignada = ?, mensaje = ?
            WHERE id = ?
        """, (
            empleado["nombre"], empleado["categoria"], empleado["foto"], empleado["mesa"],
            empleado["mesa_asignada"], empleado["mensaje"], empleado["id"]
        ))
        conn.commit()

def mover_a_finalizados(empleado):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO finalizados (id, nombre, categoria) VALUES (?, ?, ?)
        """, (empleado["id"], empleado["nombre"], empleado["categoria"]))
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
            INSERT INTO empleados (id, nombre, categoria, foto, mesa, mesa_asignada, mensaje)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            emp["id"], emp["nombre"], emp["categoria"],
            None, None, None, ""
        ))
        conn.commit()

def registrar_movimiento(nombre, categoria, accion, destino):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        zona_es = pytz.timezone("Europe/Madrid")
        ahora_local = datetime.now(zona_es)
        timestamp = ahora_local.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO movimientos (nombre, categoria, accion, destino, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, categoria, accion, destino, timestamp))
        conn.commit()

def obtener_movimientos():
    if not os.path.exists(DB_PATH):
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, categoria, accion, destino, timestamp
            FROM movimientos
            ORDER BY timestamp DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
