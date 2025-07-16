import streamlit as st
import streamlit.components.v1 as components
import uuid
import hashlib
from db_utils import (
    init_db, obtener_empleados, agregar_empleado, actualizar_empleado,
    mover_a_finalizados, obtener_finalizados
)
import os
import json
import time

st.set_page_config(layout="wide")

# ----------- AUTENTICACIÓN -----------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

USUARIOS = {
    "responsable": hash_password("admin123"),
    "usuario": hash_password("crupier123")
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None

if not st.session_state.autenticado:
    st.sidebar.title("🔐 Iniciar sesión")
    usuario = st.sidebar.text_input("Usuario")
    contrasena = st.sidebar.text_input("Contraseña", type="password")

    if usuario and contrasena:
        if usuario in USUARIOS:
            if hash_password(contrasena) == USUARIOS[usuario]:
                st.session_state.autenticado = True
                st.session_state.rol = "Responsable" if usuario == "responsable" else "Usuario"
                st.rerun()
            else:
                st.sidebar.error("❌ Contraseña incorrecta")
        else:
            st.sidebar.warning("⚠️ Usuario no encontrado")

if not st.session_state.autenticado:
    st.stop()

rol = st.session_state.rol

# ----------- BOTÓN REINICIAR JORNADA arriba a la izquierda -----------
col_reset, col_blank = st.columns([1, 9])
with col_reset:
    if st.button("🔄 Reiniciar Jornada"):
        if os.path.exists("casino.db"):
            os.remove("casino.db")
        st.success("Base de datos reiniciada.")
        st.rerun()

# Botón cerrar sesión en sidebar
with st.sidebar:
    if st.button("🔓 Cerrar sesión"):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.rerun()

# ----------- RELOJ + AUTOREFRESH -----------
def mostrar_reloj_js():
    reloj_html = """
    <div style="text-align: center;">
        <h3>🕒 <span id="reloj">--:--:--</span></h3>
    </div>
    <script>
    const reloj = document.getElementById("reloj");
    function actualizarHora() {
        const ahora = new Date();
        const horas = String(ahora.getHours()).padStart(2, '0');
        const minutos = String(ahora.getMinutes()).padStart(2, '0');
        const segundos = String(ahora.getSeconds()).padStart(2, '0');
        reloj.textContent = `${horas}:${minutos}:${segundos}`;
    }
    setInterval(actualizarHora, 1000);
    actualizarHora();
    </script>
    """
    components.html(reloj_html, height=80)

# ----------- INICIALIZACIÓN -----------
init_db()
nombres_mesas = ["RA1", "RA2", "RA3", "RA4", "BJ1", "BJ2", "PK1", "iT-PK", "iT-BJ", "TEXAS", "PB", "Mini PB"]
empleados = obtener_empleados()
finalizados = obtener_finalizados()
mesas = {nombre: [] for nombre in nombres_mesas}
for emp in empleados:
    if emp["mesa"]:
        mesas[emp["mesa"]].append(emp)

if "nombre_nuevo" not in st.session_state:
    st.session_state["nombre_nuevo"] = ""

if "categoria_nueva" not in st.session_state:
    st.session_state["categoria_nueva"] = "Seleccionar"

# ----------- SOLO PARA RESPONSABLES -----------
if rol == "Responsable":

    with st.sidebar:
        st.markdown("## ➕ Agregar empleado")
        nombre_nuevo = st.text_input("Nombre", key="nombre_nuevo")
        opciones_categoria = ["Seleccionar", "Jefe de Mesa", "Crupier de 1º", "Crupier de 2º", "Crupier de 3º"]
        categoria_nueva = st.selectbox("Categoría", opciones_categoria, key="categoria_nueva")

        if st.button("Agregar"):
            if not st.session_state["nombre_nuevo"]:
                st.warning("Por favor ingresa un nombre.")
            elif st.session_state["categoria_nueva"] == "Seleccionar":
                st.warning("Por favor selecciona una categoría válida.")
            else:
                nuevo = {
                    "id": str(uuid.uuid4()),
                    "nombre": st.session_state["nombre_nuevo"],
                    "categoria": st.session_state["categoria_nueva"],
                    "foto": None,
                    "mesa": None,
                    "mesa_asignada": None,
                    "mensaje": ""
                }
                agregar_empleado(nuevo)
                st.session_state["nombre_nuevo"] = ""
                st.session_state["categoria_nueva"] = "Seleccionar"
                st.success(f"{nuevo['nombre']} agregado a sala de descanso.")
                st.rerun()

    st.markdown("## 🃏 Área de mesas de trabajo")
    col_mesas = st.columns(4)

    for i, (nombre_mesa, empleados_mesa) in enumerate(mesas.items()):
        with col_mesas[i % 4]:
            with st.container():
                st.markdown(f"""<div style='border: 2px solid #ccc; border-radius: 12px; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9;'>
                    <h4 style='text-align: center;'>🃏 {nombre_mesa}</h4>""", unsafe_allow_html=True)
                for emp in empleados_mesa:
                    st.markdown(f"- 👤 {emp['nombre']} ({emp['categoria']})")
                    if st.button(f"❌ Liberar", key=f"lib_{emp['id']}"):
                        emp["mesa"] = None
                        actualizar_empleado(emp)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    col_descanso, col_reloj = st.columns([6, 1])
    with col_descanso:
        st.markdown("## 🛋️ Sala de descanso")
    with col_reloj:
        mostrar_reloj_js()

    if st.button("📦 ASIGNAR empleados a sus mesas"):
        for emp in empleados:
            if not emp["mesa"] and emp["mesa_asignada"]:
                emp["mesa"] = emp["mesa_asignada"]
                emp["mesa_asignada"] = None
                actualizar_empleado(emp)
        st.success("Empleados asignados.")
        st.rerun()

    for emp in empleados:
        if not emp["mesa"]:
            with st.expander(f"👤 {emp['nombre']} ({emp['categoria']})"):
                nueva_mesa_asig = st.selectbox("Asignar a mesa:", [None] + nombres_mesas,
                    index=0 if not emp["mesa_asignada"] else nombres_mesas.index(emp["mesa_asignada"]) + 1,
                    key=f"mesa_asig_{emp['id']}")
                nuevo_mensaje = st.text_input("Mensaje opcional:", value=emp["mensaje"], key=f"msg_{emp['id']}")

                if nueva_mesa_asig != emp["mesa_asignada"] or nuevo_mensaje != emp["mensaje"]:
                    emp["mesa_asignada"] = nueva_mesa_asig
                    emp["mensaje"] = nuevo_mensaje
                    actualizar_empleado(emp)
                    st.rerun()

                if st.button("🛑 Finalizar jornada", key=f"fin_{emp['id']}"):
                    mover_a_finalizados(emp)
                    st.rerun()

# ----------- COMPONENTE ASIGNACIONES PENDIENTES CON AUTOREFRESH JS -----------

def render_asignaciones_pendientes():
    # Recarga empleados para reflejar cambios en DB
    empleados_actualizados = obtener_empleados()
    asignaciones = [emp for emp in empleados_actualizados if not emp["mesa"] and emp["mesa_asignada"]]

    html = "<div id='asignaciones-pendientes'>"
    if asignaciones:
        for emp in asignaciones:
            msg = f"<i>Mensaje: {emp['mensaje']}</i>" if emp['mensaje'] else ""
            html += f"<div style='padding:5px; border-bottom:1px solid #ddd;'>{emp['nombre']} será enviado a <b>{emp['mesa_asignada']}</b>. {msg}</div>"
    else:
        html += "<div>No hay asignaciones pendientes</div>"
    html += "</div>"
    return html

# HTML + JS para refrescar esa parte cada 5 segundos
auto_refresh_html = """
<div id="asignaciones-container">
    %s
</div>
<script>
async function refreshAsignaciones(){
    const res = await fetch("/streamlit_asignaciones");
    const text = await res.text();
    document.getElementById("asignaciones-container").innerHTML = text;
}
setInterval(refreshAsignaciones, 5000);
</script>
""" % render_asignaciones_pendientes()

# Función para servir contenido en la ruta /streamlit_asignaciones
# Esto requiere usar st.experimental_get_query_params + componentes para hacer un mini API local
# Pero Streamlit no soporta rutas custom sin FastAPI o similar,
# así que usaremos una solución simple: re-renderizamos el componente con JS que recarga todo el bloque.

# Entonces, para evitar complicaciones, vamos a usar un iframe que recarga la lista cada 5s:

iframe_html = f"""
<iframe srcdoc='{render_asignaciones_pendientes().replace("'", "&apos;")}' 
    style='border:none; width:100%; height:150px;' id='iframe-asignaciones'></iframe>
<script>
setInterval(() => {{
    const iframe = document.getElementById('iframe-asignaciones');
    iframe.srcdoc = `{render_asignaciones_pendientes().replace("`", "\\`")}`;
}}, 5000);
</script>
"""

st.markdown("### 📝 Asignaciones pendientes")
components.html(iframe_html, height=180)

# ----------- FINALIZARON JORNADA (SOLO RESPONSABLE) -----------
with st.sidebar:
    if rol == "Responsable":
        if finalizados:
            st.markdown("#### ✅ Finalizaron jornada")
            for emp in finalizados:
                st.markdown(f"- 👋 {emp['nombre']} ({emp['categoria']})")
