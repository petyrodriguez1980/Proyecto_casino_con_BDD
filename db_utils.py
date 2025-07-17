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
    from tinydb import TinyDB, Query
    db = TinyDB("casino.db")
    finalizados = db.table("finalizados")
    empleados = db.table("empleados")

    finalizados.remove(Query().id == emp["id"])
    
    # Restauramos al estado de descanso
    emp["mesa"] = None
    emp["mesa_asignada"] = None
    emp["mensaje"] = ""
    empleados.insert(emp)
