import sqlite3
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

def registrar_movimiento(nombre, categoria, accion, destino):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
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
        cursor.execute("""
            INSERT INTO movimientos (nombre, categoria, accion, destino)
            VALUES (?, ?, ?, ?)
        """, (nombre, categoria, accion, destino))
        conn.commit()
