import sqlite3
from datetime import datetime
import os

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

        # Eliminamos de finalizados
        cursor.execute("DELETE FROM finalizados WHERE id = ?", (emp["id"],))

        # Restauramos en sala de descanso
        cursor.execute("""
            INSERT INTO empleados (id, nombre, categoria, foto, mesa, mesa_asignada, mensaje)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            emp["id"], emp["nombre"], emp["categoria"],
            None,  # foto
            None,  # mesa
            None,  # mesa_asignada
            ""     # mensaje
        ))
        conn.commit()

def registrar_movimiento(empleado_id, nombre, categoria, accion, destino=None):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id TEXT,
            nombre TEXT,
            categoria TEXT,
            accion TEXT,
            destino TEXT,
            timestamp DATETIME
        )
    """)
    c.execute("""
        INSERT INTO movimientos (empleado_id, nombre, categoria, accion, destino, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (empleado_id, nombre, categoria, accion, destino, datetime.now()))
    conn.commit()
    conn.close()

# Ejemplo de uso en tu app:
# registrar_movimiento(emp['id'], emp['nombre'], emp['categoria'], "Asignado a mesa", emp['mesa'])
# registrar_movimiento(emp['id'], emp['nombre'], emp['categoria'], "Finalizó jornada")
# registrar_movimiento(emp['id'], emp['nombre'], emp['categoria'], "Liberado de mesa", emp['mesa'])
# registrar_movimiento(emp['id'], emp['nombre'], emp['categoria'], "Reingresado a sala de descanso")

# Función para consultar movimientos

def obtener_movimientos():
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT nombre, categoria, accion, destino, timestamp FROM movimientos ORDER BY timestamp DESC")
    movimientos = c.fetchall()
    conn.close()
    return movimientos
