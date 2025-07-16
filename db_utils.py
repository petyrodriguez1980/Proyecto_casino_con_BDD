import sqlite3

DB_PATH = "empleados.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS empleados (
            id TEXT PRIMARY KEY,
            nombre TEXT,
            categoria TEXT,
            foto TEXT,
            mesa TEXT,
            mesa_asignada TEXT,
            mensaje TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS finalizados (
            id TEXT PRIMARY KEY,
            nombre TEXT,
            categoria TEXT
        )''')
        conn.commit()

def obtener_empleados():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM empleados")
        rows = c.fetchall()
        cols = [column[0] for column in c.description]
        return [dict(zip(cols, row)) for row in rows]

def agregar_empleado(emp):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO empleados VALUES (?, ?, ?, ?, ?, ?, ?)", (
            emp["id"], emp["nombre"], emp["categoria"],
            emp["foto"], emp["mesa"], emp["mesa_asignada"], emp["mensaje"]
        ))
        conn.commit()

def actualizar_empleado(emp):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''UPDATE empleados SET nombre=?, categoria=?, foto=?, mesa=?, mesa_asignada=?, mensaje=?
                     WHERE id=?''', (
            emp["nombre"], emp["categoria"], emp["foto"],
            emp["mesa"], emp["mesa_asignada"], emp["mensaje"], emp["id"]
        ))
        conn.commit()

def eliminar_empleado(emp_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM empleados WHERE id=?", (emp_id,))
        conn.commit()

def mover_a_finalizados(emp):
    eliminar_empleado(emp["id"])
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO finalizados VALUES (?, ?, ?)", (
            emp["id"], emp["nombre"], emp["categoria"]
        ))
        conn.commit()

def obtener_finalizados():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM finalizados")
        rows = c.fetchall()
        cols = [column[0] for column in c.description]
        return [dict(zip(cols, row)) for row in rows]
