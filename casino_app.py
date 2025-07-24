import streamlit as st
import streamlit.components.v1 as components
import uuid
import hashlib
from random import randint
from db_utils import (
    init_db, obtener_empleados, agregar_empleado, actualizar_empleado,
    mover_a_finalizados, obtener_finalizados, registrar_movimiento, reingresar_empleado,
    obtener_movimientos, obtener_empleados_en_mesa
)
import os

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

if "equipo_hoy" not in st.session_state:
    st.session_state.equipo_hoy = []

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

# Botón cerrar sesión
with st.sidebar:
    if st.button("🔓 Cerrar sesión"):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.rerun()


# ----------- RELOJ JAVASCRIPT -----------
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

opciones_envio = nombres_mesas + ["Sala de descanso", "Finalizar jornada"]

empleados = obtener_empleados()
finalizados = obtener_finalizados()
mesas = {nombre: [] for nombre in nombres_mesas}
for emp in empleados:
    if emp["mesa"]:
        mesas[emp["mesa"].strip()].append(emp)

# ----------- VISTA PARA RESPONSABLE -----------
if rol == "Responsable":

    if st.session_state.get("limpiar_campos", False):
        st.session_state["nombre_nuevo"] = ""
        st.session_state["categoria_nueva"] = "Seleccionar"
        st.session_state["limpiar_campos"] = False

    with st.sidebar:
        st.markdown("## ➕ Agregar empleado")
        nombre_nuevo = st.text_input("Nombre", key="nombre_nuevo")
        opciones_categoria = ["Seleccionar", "Jefe de Mesa", "Crupier de 1º", "Crupier de 2º", "Crupier de 3º"]
        categoria_nueva = st.selectbox("Categoría", opciones_categoria, key="categoria_nueva")

        if st.button("Agregar"):
            if not nombre_nuevo:
                st.warning("Por favor ingresa un nombre.")
            elif categoria_nueva == "Seleccionar":
                st.warning("Por favor selecciona una categoría válida.")
            else:
                nuevo = {
                    "id": str(uuid.uuid4()), "nombre": nombre_nuevo, "categoria": categoria_nueva,
                    "foto": None, "mesa": None, "mesa_asignada": None, "mensaje": ""
                }

                # Solo agregar al equipo_hoy (no a la base de datos todavía)
                st.session_state.equipo_hoy.append(nuevo)
                st.success(f"{nombre_nuevo} agregado temporalmente al equipo de hoy.")
                st.session_state.limpiar_campos = True
                st.rerun()

    col_area, col_reiniciar = st.columns([6, 1])
    with col_area:
        st.markdown("## 🃏 Área de mesas de trabajo")
    with col_reiniciar:
        if st.button("🔄 Reiniciar Jornada"):
            if os.path.exists("casino.db"):
                os.remove("casino.db")
            st.session_state.equipo_hoy = []  # Limpiar empleados temporales
            st.success("Base de datos reiniciada.")
            st.rerun()

    col_mesas = st.columns(4)
    for i, (nombre_mesa, empleados_mesa) in enumerate(mesas.items()):
        with col_mesas[i % 4]:
            with st.container():
                st.markdown(f"""<div style='border: 2px solid #ccc; border-radius: 12px; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9;'>
                <h4 style='text-align: center;'>🃏 {nombre_mesa}</h4>""", unsafe_allow_html=True)

                for emp in empleados_mesa:
                    emp_id = str(emp.get("id") or str(uuid.uuid4()))
                    expander_key = f"expander_{emp_id}"

                    if expander_key not in st.session_state or not isinstance(st.session_state[expander_key], bool):
                        st.session_state[expander_key] = False

                    nombre = emp.get("nombre") or "Sin nombre"
                    categoria = emp.get("categoria") or "Sin categoría"
                    titulo_expander = f"👤 {nombre} ({categoria})"

                    try:
                        with st.expander(titulo_expander, expanded=st.session_state[expander_key]):
                            nueva_opcion = st.selectbox("Selecciona destino", opciones_envio, key=f"enviar_a_{emp_id}")
                            if st.button("Confirmar", key=f"confirmar_envio_{emp_id}"):
                                if nueva_opcion == "Sala de descanso":
                                    registrar_movimiento(nombre, categoria, "Liberado", "Sala de descanso")
                                    emp["mesa"] = None
                                    actualizar_empleado(emp)
                                elif nueva_opcion == "Finalizar jornada":
                                    registrar_movimiento(nombre, categoria, "Finalizó", "-")
                                    mover_a_finalizados(emp)
                                else:
                                    registrar_movimiento(nombre, categoria, "Asignado", nueva_opcion)
                                    emp["mesa"] = nueva_opcion
                                    actualizar_empleado(emp)

                                # 🔐 Cierra todos los expanders de la mesa actual
                                for emp2 in empleados_mesa:
                                    st.session_state[f"expander_{emp2['id']}"] = False

                                st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear expander: {e}")
                        st.write(
                            f"expander_key: {expander_key}, valor en session_state: {st.session_state.get(expander_key)}")

                st.markdown("</div>", unsafe_allow_html=True)

    # SALA DESCANSO + TIEMPO EN MESA

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<h4 style='color:#444;'>🛋️ Sala de descanso</h4>", unsafe_allow_html=True)
        if st.button("📦 ASIGNAR empleados a sus mesas"):
            ids_asignados = []
            for emp in empleados:
                if not emp["mesa"] and emp["mesa_asignada"]:
                    registrar_movimiento(emp["nombre"], emp["categoria"], "Asignado", emp["mesa_asignada"])
                    emp["mesa"] = emp["mesa_asignada"]
                    emp["mesa_asignada"] = None
                    emp["mensaje"] = ""
                    actualizar_empleado(emp)
                    ids_asignados.append(emp["id"])

            st.session_state["limpiar_mensajes_ids"] = ids_asignados
            st.success("Empleados asignados.")
            st.rerun()

        if "limpiar_mensajes_ids" in st.session_state:
            for emp in empleados:
                if emp["id"] in st.session_state["limpiar_mensajes_ids"]:
                    st.session_state[f"msg_{emp['id']}"] = ""
            del st.session_state["limpiar_mensajes_ids"]

        for emp in empleados:
            if not emp["mesa"]:
                with st.expander(f"👤 {emp['nombre']} ({emp['categoria']})"):
                    nueva_mesa_asig = st.selectbox("Asignar a mesa:", [None] + nombres_mesas,
                                                   index=0 if not emp["mesa_asignada"] else nombres_mesas.index(
                                                       emp["mesa_asignada"]) + 1,
                                                   key=f"mesa_asig_{emp['id']}")
                    nuevo_mensaje = st.text_input("Mensaje opcional:", value=emp["mensaje"], key=f"msg_{emp['id']}")

                    if nueva_mesa_asig != emp["mesa_asignada"] or nuevo_mensaje != emp["mensaje"]:
                        emp["mesa_asignada"] = nueva_mesa_asig
                        emp["mensaje"] = nuevo_mensaje
                        actualizar_empleado(emp)
                        st.rerun()

                    if st.button("🛑 Finalizar jornada", key=f"fin_{emp['id']}"):
                        registrar_movimiento(emp["nombre"], emp["categoria"], "Finalizó", "-")
                        mover_a_finalizados(emp)
                        st.rerun()

    with col2:
        # ----------- TIEMPO EN MESA (a la derecha de Sala de descanso) -----------
        with col2:
            st.markdown("""
            <div style='
                font-size: 1.2rem;
                color: darkgreen;
                font-weight: bold;
                text-decoration: underline;
                display: flex;
                align-items: center;
            '>
                ⏱️ Tiempo en mesa
            </div>
            """, unsafe_allow_html=True)

            empleados_en_mesa = obtener_empleados_en_mesa()

            contenedor_html = """
            <div>
            """

            for emp in empleados_en_mesa.values():
                nombre = emp['nombre']
                categoria = emp['categoria']
                destino = emp['destino']
                hora_js = emp["hora"].strftime("%Y-%m-%dT%H:%M:%S")  # formato compatible con Date()

                contenedor_html += f"""
                <div style="margin-bottom: 8px;">
                    ♠️ <strong>{nombre}</strong> ({categoria}) - {destino} - 
                    <span class="tiempo-transcurrido" data-hora-ingreso="{hora_js}">Cargando...</span>
                </div>
                """

            contenedor_html += """
            <script>
            function actualizarTiempos() {
                const elementos = document.querySelectorAll(".tiempo-transcurrido");
                elementos.forEach(el => {
                    const horaIngreso = new Date(el.dataset.horaIngreso);
                    const ahora = new Date();
                    const diffMs = ahora - horaIngreso;

                    const totalSegundos = Math.floor(diffMs / 1000);
                    const horas = Math.floor(totalSegundos / 3600);
                    const minutos = Math.floor((totalSegundos % 3600) / 60);
                    const segundos = totalSegundos % 60;

                    const formato = 
                        (horas > 0 ? `${horas}h ` : "") +
                        (minutos > 0 ? `${minutos}m ` : "") +
                        `${segundos}s`;

                    el.textContent = `En mesa hace ${formato}`;
                });
            }

            setInterval(actualizarTiempos, 1000);
            actualizarTiempos();
            </script>
            </div>
            """

            components.html(contenedor_html, height=300, scrolling=True)

    with st.sidebar:
        if st.session_state.equipo_hoy:
            st.markdown("""
            <div style='
                font-size: 1.2rem;
                color: green;
                font-weight: bold;
                text-decoration: underline;
                display: flex;
                align-items: center;
            '>
                <span style="margin-right: 6px;">👥</span> EQUIPO DE HOY
            </div>
            """, unsafe_allow_html=True)
            for emp in st.session_state.equipo_hoy:
                st.markdown(f"**👤 {emp['nombre']} ({emp['categoria']})**")

                destino = st.selectbox("Enviar a:", opciones_envio, key=f"destino_equipo_{emp['id']}")
                if st.button("Confirmar", key=f"confirmar_equipo_{emp['id']}"):
                    accion = "Asignado" if destino not in ["Sala de descanso", "Finalizar jornada"] else (
                        "Liberado" if destino == "Sala de descanso" else "Finalizó"
                    )
                    registrar_movimiento(emp["nombre"], emp["categoria"], accion, destino)

                    if destino == "Finalizar jornada":
                        mover_a_finalizados(emp)
                    else:
                        emp["mesa"] = None if destino == "Sala de descanso" else destino
                        agregar_empleado(emp)

                    st.session_state.equipo_hoy = [e for e in st.session_state.equipo_hoy if e["id"] != emp["id"]]
                    st.rerun()

        if finalizados:
            st.markdown("## 💤 Finalizaron jornada")

            finalizados = obtener_finalizados()
            opciones_envio = nombres_mesas + ["Sala de descanso", "Finalizar jornada"]

            for f in finalizados:
                st.markdown(f"**👤 {f['nombre']} ({f['categoria']})**")

                clave_destino = f"select_reingreso_{f['id']}"

                if clave_destino not in st.session_state:
                    st.session_state[clave_destino] = "RA1"

                # Mostrar selectbox (valor actual del estado)
                destino_seleccionado = st.selectbox(
                    "Reingresar a:",
                    opciones_envio[:-1],
                    key=clave_destino,
                    index=opciones_envio[:-1].index(st.session_state[clave_destino])
                )

                # Solo procesar si se hace clic en el botón
                if st.button("Reingresar", key=f"reingresar_{f['id']}"):
                    # Leer el valor actual desde session_state
                    destino_real = st.session_state.get(clave_destino)
                    if destino_real:
                        f["mesa"] = None if destino_real == "Sala de descanso" else destino_real
                        reingresar_empleado(f)
                        registrar_movimiento(f["nombre"], f["categoria"], "Asignado", destino_real)
                        st.success(f"{f['nombre']} fue reingresado a {destino_real}")
                        del st.session_state[clave_destino]
                        st.rerun()

col_asig, col_btn_actualizar, col_reloj = st.columns([6, 6, 2])
with col_asig:
    st.markdown("### 📝 Asignaciones pendientes")
with col_reloj:
    mostrar_reloj_js()
with col_btn_actualizar:
    if st.session_state.rol == "Usuario":
        if st.button("ACTUALIZAR"):
            st.rerun()

for emp in empleados:
    if not emp["mesa"] and emp["mesa_asignada"]:
        st.info(f"{emp['nombre']} será enviado a **{emp['mesa_asignada']}**. " +
                (f"Mensaje: {emp['mensaje']} " if emp['mensaje'] else ""))

if rol == "Responsable":
    st.markdown("---")
    st.markdown("## 📜 Historial de movimientos")

    movimientos = obtener_movimientos()

    if not movimientos:
        st.info("No hay movimientos registrados.")
    else:
        import pandas as pd

        df_mov = pd.DataFrame(movimientos)
        df_mov["timestamp"] = pd.to_datetime(df_mov["timestamp"])
        df_mov = df_mov.sort_values("timestamp", ascending=False)

        col1, col2 = st.columns(2)

        nombres_unicos = sorted(df_mov["nombre"].dropna().unique())

        with col1:
            filtro_nombre = st.selectbox("Filtrar por nombre", ["Todos"] + nombres_unicos)

        with col2:
            filtro_accion = st.selectbox("Filtrar por acción", ["Todas"] + sorted(df_mov["accion"].dropna().unique()))

        if filtro_nombre != "Todos":
            df_mov = df_mov[df_mov["nombre"] == filtro_nombre]

        if filtro_accion != "Todas":
            df_mov = df_mov[df_mov["accion"] == filtro_accion]

        st.dataframe(
            df_mov[["timestamp", "nombre", "categoria", "accion", "destino"]].rename(columns={
                "timestamp": "Fecha y hora",
                "nombre": "Empleado",
                "categoria": "Categoría",
                "accion": "Acción",
                "destino": "Destino"
            }),
            use_container_width=True,
            hide_index=True
        )