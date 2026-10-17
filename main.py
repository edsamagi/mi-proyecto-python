import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# ---------------------------------------------------------
# CONFIGURACIÓN DE CONEXIÓN A MYSQL
# ---------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123qwe",  
    "database": "compumep_db"
}

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)

CATALOGO_SERVICIOS = {}
servicios_seleccionados = []

def cargar_catalogo():
    global CATALOGO_SERVICIOS
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_servicio, nombre_servicio, nivel_semaforo, tiempo_estimado FROM catalogo_servicios;")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        CATALOGO_SERVICIOS = {}
        for fila in filas:
            CATALOGO_SERVICIOS[fila[1]] = {
                "id": fila[0],
                "semaforo": fila[2],
                "tiempo": fila[3]
            }
    except Exception as error:
        print(f"Error cargando catálogo: {error}")
        messagebox.showerror("Error MySQL", f"No se pudo cargar el catálogo de servicios:\n{error}")

# ---------------------------------------------------------
# GESTIÓN DE SERVICIOS EN INTERFAZ
# ---------------------------------------------------------
def agregar_servicio_a_lista():
    serv = cmb_servicio.get()
    if not serv or serv not in CATALOGO_SERVICIOS:
        messagebox.showwarning("Atención", "Seleccione un servicio válido del catálogo.")
        return
    
    if serv in servicios_seleccionados:
        messagebox.showinfo("Información", "Este servicio ya fue agregado a la lista.")
        return

    servicios_seleccionados.append(serv)
    actualizar_lista_servicios_ui()

def quitar_servicio_de_lista():
    seleccion = lst_servicios.curselection()
    if seleccion:
        indice = seleccion[0]
        servicios_seleccionados.pop(indice)
        actualizar_lista_servicios_ui()

def actualizar_lista_servicios_ui():
    lst_servicios.delete(0, tk.END)
    for s in servicios_seleccionados:
        info = CATALOGO_SERVICIOS[s]
        lst_servicios.insert(tk.END, f"• [{info['semaforo']}] {s} ({info['tiempo']})")

def limpiar_formulario():
    servicios_seleccionados.clear()
    actualizar_lista_servicios_ui()
    
    txt_orden.delete(0, tk.END)
    txt_serial.delete(0, tk.END)
    txt_serial.insert(0, "N/A")
    txt_marca.delete(0, tk.END)
    txt_modelo.delete(0, tk.END)
    txt_estado_fisico.delete(0, tk.END)
    txt_estado_fisico.insert(0, "Sin daños visibles aparentes")
    
    txt_falla_cliente.delete("1.0", tk.END)
    txt_prediagnostico.delete("1.0", tk.END)
    txt_diagnostico.delete("1.0", tk.END)
    txt_solucion.delete("1.0", tk.END)
    txt_observaciones.delete("1.0", tk.END)
    
    cmb_tipo.current(0)
    cmb_urgencia.current(0)
    cmb_estado_orden.current(0)
    cmb_smart.current(0)
    if CATALOGO_SERVICIOS:
        cmb_servicio.current(0)
    actualizar_semaforo()
    txt_orden.focus()

# ---------------------------------------------------------
# COPIAR REPORTE AL PORTAPAPELES (PARA EL SOFTWARE WEB)
# ---------------------------------------------------------
def copiar_reporte_web():
    orden = txt_orden.get().strip().upper()
    if not orden:
        messagebox.showwarning("Atención", "Ingrese o cargue una orden para generar el reporte.")
        return

    tipo = cmb_tipo.get()
    marca = txt_marca.get().strip()
    modelo = txt_modelo.get().strip()
    falla_cli = txt_falla_cliente.get("1.0", tk.END).strip()
    prediag = txt_prediagnostico.get("1.0", tk.END).strip()
    diag = txt_diagnostico.get("1.0", tk.END).strip()
    solucion = txt_solucion.get("1.0", tk.END).strip()
    obs = txt_observaciones.get("1.0", tk.END).strip()
    smart = cmb_smart.get()
    estado = cmb_estado_orden.get()

    servicios_txt = ", ".join(servicios_seleccionados) if servicios_seleccionados else "Pendiente por autorizar"

    resumen = (
        f"--- REPORTE TÉCNICO COMPUMEP (ORDEN: {orden}) ---\n"
        f"EQUIPO: {tipo} {marca} {modelo}\n"
        f"ESTADO EN TALLER: {estado}\n"
        f"FALLA REPORTADA: {falla_cli}\n"
        f"ESTADO SMART: {smart}\n"
        f"PREDIAGNÓSTICO INICIAL (MESA): {prediag or 'N/A'}\n"
        f"DIAGNÓSTICO TÉCNICO: {diag or 'En proceso'}\n"
        f"SERVICIOS ASIGNADOS: {servicios_txt}\n"
        f"SOLUCIÓN / TRABAJO REALIZADO: {solucion or 'En banco'}\n"
        f"OBSERVACIONES / SALVEDADES: {obs or 'Sin salvedades de garantía'}\n"
        f"------------------------------------------------"
    )

    ventana.clipboard_clear()
    ventana.clipboard_append(resumen)
    messagebox.showinfo("Copiado al Portapapeles", "Reporte técnico copiado.\nPuedes pegarlo con Ctrl + V directamente en el software web de la empresa.")

# ---------------------------------------------------------
# MONITOR EN VIVO Y EVENTO DOBLE CLIC
# ---------------------------------------------------------
def cargar_tabla_monitoreo():
    for fila in tree_ordenes.get_children():
        tree_ordenes.delete(fila)
        
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                o.id_orden,
                o.urgencia,
                CONCAT(e.marca, ' ', e.modelo) AS equipo,
                o.estado,
                COALESCE(MIN(c.nivel_semaforo), 'Sin servicio') AS semaforo_ppal
            FROM ORDENES_SERVICIO o
            JOIN EQUIPOS e ON o.id_equipo = e.id_equipo
            LEFT JOIN FICHAS_TECNICAS f ON o.id_orden = f.id_orden
            LEFT JOIN DETALLE_SERVICIOS_FICHA d ON f.id_ficha = d.id_ficha
            LEFT JOIN CATALOGO_SERVICIOS c ON d.id_servicio = c.id_servicio
            GROUP BY o.id_orden, o.urgencia, e.marca, e.modelo, o.estado
            ORDER BY 
                CASE 
                    WHEN o.urgencia LIKE '%Urgente%' THEN 1
                    WHEN o.urgencia LIKE '%Media%' THEN 2
                    ELSE 3
                END ASC,
                CASE 
                    WHEN COALESCE(MIN(c.nivel_semaforo), '') = 'Verde' THEN 1
                    WHEN COALESCE(MIN(c.nivel_semaforo), '') = 'Amarillo' THEN 2
                    WHEN COALESCE(MIN(c.nivel_semaforo), '') = 'Rojo' THEN 3
                    ELSE 4
                END ASC,
                o.fecha_ingreso DESC;
        """
        cursor.execute(consulta)
        registros = cursor.fetchall()
        cursor.close()
        conexion.close()

        for reg in registros:
            tree_ordenes.insert("", tk.END, values=(
                reg["id_orden"],
                reg["urgencia"],
                reg["equipo"],
                reg["semaforo_ppal"],
                reg["estado"]
            ))
    except Exception as err:
        print(f"Error al cargar tabla en vivo: {err}")

def al_hacer_doble_clic(event):
    item_seleccionado = tree_ordenes.selection()
    if not item_seleccionado:
        return
    valores = tree_ordenes.item(item_seleccionado[0], "values")
    id_orden = valores[0]
    txt_orden.delete(0, tk.END)
    txt_orden.insert(0, id_orden)
    buscar_orden()

# ---------------------------------------------------------
# LÓGICA DE NEGOCIO: BUSCAR Y GUARDAR / ACTUALIZAR
# ---------------------------------------------------------
def buscar_orden():
    orden = txt_orden.get().strip().upper()
    if not orden:
        messagebox.showwarning("Atención", "Ingrese un número de orden para buscar.")
        return

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        consulta = """
            SELECT o.id_orden, o.urgencia, o.estado, o.falla_cliente, o.estado_fisico,
                   e.tipo_equipo, e.marca, e.modelo, e.serial,
                   f.id_ficha, f.salud_smart,
                   f.prediagnostico_inicial, f.diagnostico_definitivo,
                   f.solucion_tecnica, f.observaciones_garantia
            FROM ORDENES_SERVICIO o
            JOIN EQUIPOS e ON o.id_equipo = e.id_equipo
            LEFT JOIN FICHAS_TECNICAS f ON o.id_orden = f.id_orden
            WHERE o.id_orden = %s;
        """
        cursor.execute(consulta, (orden,))
        registro = cursor.fetchone()

        if registro:
            cmb_tipo.set(registro["tipo_equipo"])
            txt_marca.delete(0, tk.END)
            txt_marca.insert(0, registro["marca"])
            txt_modelo.delete(0, tk.END)
            txt_modelo.insert(0, registro["modelo"])
            txt_serial.delete(0, tk.END)
            txt_serial.insert(0, registro["serial"])

            txt_estado_fisico.delete(0, tk.END)
            txt_estado_fisico.insert(0, registro["estado_fisico"])

            txt_falla_cliente.delete("1.0", tk.END)
            txt_falla_cliente.insert("1.0", registro["falla_cliente"])

            if registro["urgencia"]:
                cmb_urgencia.set(registro["urgencia"])
            if registro["estado"]:
                cmb_estado_orden.set(registro["estado"])
            if registro["salud_smart"]:
                cmb_smart.set(registro["salud_smart"])

            txt_prediagnostico.delete("1.0", tk.END)
            if registro["prediagnostico_inicial"]:
                txt_prediagnostico.insert("1.0", registro["prediagnostico_inicial"])

            txt_diagnostico.delete("1.0", tk.END)
            if registro["diagnostico_definitivo"]:
                txt_diagnostico.insert("1.0", registro["diagnostico_definitivo"])

            txt_solucion.delete("1.0", tk.END)
            if registro["solucion_tecnica"]:
                txt_solucion.insert("1.0", registro["solucion_tecnica"])

            txt_observaciones.delete("1.0", tk.END)
            if registro["observaciones_garantia"]:
                txt_observaciones.insert("1.0", registro["observaciones_garantia"])

            # Cargar servicios asociados previamente
            servicios_seleccionados.clear()
            if registro["id_ficha"]:
                sql_servicios = """
                    SELECT c.nombre_servicio 
                    FROM DETALLE_SERVICIOS_FICHA d
                    JOIN CATALOGO_SERVICIOS c ON d.id_servicio = c.id_servicio
                    WHERE d.id_ficha = %s;
                """
                cursor.execute(sql_servicios, (registro["id_ficha"],))
                for f_serv in cursor.fetchall():
                    servicios_seleccionados.append(f_serv["nombre_servicio"])
                actualizar_lista_servicios_ui()

        else:
            messagebox.showinfo("No Encontrada", f"La orden {orden} no existe en la base de datos.")

        cursor.close()
        conexion.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error al consultar MySQL:\n{err}")

def guardar_o_actualizar_ficha():
    orden = txt_orden.get().strip().upper()
    urgencia = cmb_urgencia.get()
    tipo = cmb_tipo.get()
    marca = txt_marca.get().strip()
    modelo = txt_modelo.get().strip()
    serial = txt_serial.get().strip() or "N/A"
    falla_cli = txt_falla_cliente.get("1.0", tk.END).strip()
    est_fisico = txt_estado_fisico.get().strip() or "Sin daños visibles aparentes"
    smart = cmb_smart.get()
    estado_orden = cmb_estado_orden.get()
    prediag = txt_prediagnostico.get("1.0", tk.END).strip()
    diag = txt_diagnostico.get("1.0", tk.END).strip()
    solucion = txt_solucion.get("1.0", tk.END).strip()
    obs = txt_observaciones.get("1.0", tk.END).strip()

    if not orden or not marca or not modelo or not falla_cli:
        messagebox.showwarning("Campos Requeridos", "Debe ingresar como mínimo: N° Orden, Marca, Modelo y Falla reportada.")
        return

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        fecha_actual = datetime.now()

        cursor.execute("SELECT id_orden, id_equipo FROM ORDENES_SERVICIO WHERE id_orden = %s;", (orden,))
        existe = cursor.fetchone()

        if not existe:
            # 1. INSERTAR NUEVO REGISTRO
            cursor.execute("INSERT INTO EQUIPOS (tipo_equipo, marca, modelo, serial) VALUES (%s, %s, %s, %s);",
                           (tipo, marca, modelo, serial))
            id_equipo = cursor.lastrowid

            cursor.execute("""
                INSERT INTO ORDENES_SERVICIO (id_orden, id_equipo, fecha_ingreso, estado, falla_cliente, estado_fisico, urgencia)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (orden, id_equipo, fecha_actual, estado_orden, falla_cli, est_fisico, urgencia))

            cursor.execute("""
                INSERT INTO FICHAS_TECNICAS (id_orden, salud_smart, prediagnostico_inicial, 
                                            diagnostico_definitivo, solucion_tecnica, observaciones_garantia, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (orden, smart, prediag, diag, solucion, obs, fecha_actual))
            id_ficha = cursor.lastrowid

            for serv in servicios_seleccionados:
                id_serv = CATALOGO_SERVICIOS[serv]["id"]
                cursor.execute("INSERT INTO DETALLE_SERVICIOS_FICHA (id_ficha, id_servicio) VALUES (%s, %s);", (id_ficha, id_serv))
            accion = "registrada"

        else:
            # 2. ACTUALIZAR REGISTRO EXISTENTE
            id_equipo = existe[1]
            cursor.execute("UPDATE EQUIPOS SET tipo_equipo=%s, marca=%s, modelo=%s, serial=%s WHERE id_equipo=%s;",
                           (tipo, marca, modelo, serial, id_equipo))

            cursor.execute("""
                UPDATE ORDENES_SERVICIO 
                SET estado=%s, falla_cliente=%s, estado_fisico=%s, urgencia=%s 
                WHERE id_orden=%s;
            """, (estado_orden, falla_cli, est_fisico, urgencia, orden))

            cursor.execute("""
                UPDATE FICHAS_TECNICAS 
                SET salud_smart=%s, prediagnostico_inicial=%s, 
                    diagnostico_definitivo=%s, solucion_tecnica=%s, observaciones_garantia=%s, fecha_registro=%s
                WHERE id_orden=%s;
            """, (smart, prediag, diag, solucion, obs, fecha_actual, orden))

            cursor.execute("SELECT id_ficha FROM FICHAS_TECNICAS WHERE id_orden = %s;", (orden,))
            id_ficha = cursor.fetchone()[0]

            for serv in servicios_seleccionados:
                id_serv = CATALOGO_SERVICIOS[serv]["id"]
                cursor.execute("""
                    INSERT INTO DETALLE_SERVICIOS_FICHA (id_ficha, id_servicio)
                    SELECT %s, %s WHERE NOT EXISTS (
                        SELECT 1 FROM DETALLE_SERVICIOS_FICHA WHERE id_ficha = %s AND id_servicio = %s
                    );
                """, (id_ficha, id_serv, id_ficha, id_serv))
            accion = "actualizada"

        conexion.commit()
        cursor.close()
        conexion.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Error de Base de Datos", f"Ocurrió un error en MySQL:\n{err}")
        return

    # Generación de la ficha imprimible de taller
    os.makedirs("fichas_imprimibles", exist_ok=True)
    nombre_archivo = f"fichas_imprimibles/Ficha_{orden}.txt"

    txt_servicios_bloque = ""
    for s in servicios_seleccionados:
        inf = CATALOGO_SERVICIOS[s]
        txt_servicios_bloque += f"  • {s} | Semáforo: {inf['semaforo']} | Estimado: {inf['tiempo']}\n"

    contenido = (
        "============================================================\n"
        "           COMPUMEP - SOPORTE TÉCNICO Y MANTENIMIENTO        \n"
        "                 FICHA DE LABORATORIO TÉCNICO               \n"
        "============================================================\n"
        f"N° Orden de Servicio : {orden}\n"
        f"Nivel de Urgencia    : {urgencia}\n"
        f"Fecha de Registro    : {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Dispositivo          : {tipo} - {marca} {modelo} (S/N: {serial})\n"
        f"Estado Físico Entrada: {est_fisico}\n"
        "------------------------------------------------------------\n"
        f"FALLA REPORTADA POR EL CLIENTE:\n{falla_cli}\n"
        "------------------------------------------------------------\n"
        "PREDIAGNÓSTICO EN MESA (FILTRO INICIAL 10-15 MIN):\n"
        f"Telemetría SMART     : {smart}\n"
        f"Detalle Prediagnóstico:\n{prediag or 'Sin observaciones adicionales de entrada.'}\n"
        "------------------------------------------------------------\n"
        f"SERVICIOS OFICIALES APLICADOS ({len(servicios_seleccionados)}):\n"
        f"{txt_servicios_bloque or '  • Pendiente de autorización/asignación.\n'}"
        "------------------------------------------------------------\n"
        f"DIAGNÓSTICO TÉCNICO DEFINITIVO (CAUSA RAÍZ):\n{diag or 'En proceso de laboratorio.'}\n"
        "------------------------------------------------------------\n"
        f"SOLUCIÓN / TRABAJO REALIZADO:\n{solucion or 'En banco de trabajo.'}\n"
        "------------------------------------------------------------\n"
        f"OBSERVACIONES Y SALVEDADES DE GARANTÍA:\n{obs or 'Sin salvedades adicionales.'}\n"
        "============================================================\n"
        f"Estado Operativo Final: {estado_orden}\n"
        "Firma Técnico Responsable: _______________________________\n"
    )

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(contenido)

    messagebox.showinfo(
        "Operación Exitosa",
        f"Ficha {orden} {accion} correctamente.\n\n"
        "✓ Datos sincronizados en MySQL compumep_db\n"
        f"✓ Comprobante generado en: {nombre_archivo}"
    )

    cargar_tabla_monitoreo()
    limpiar_formulario()

# ---------------------------------------------------------
# INTERFAZ GRÁFICA
# ---------------------------------------------------------
cargar_catalogo()

ventana = tk.Tk()
ventana.title("Compumep - Sistema de Control y Trazabilidad de Laboratorio")
ventana.geometry("1240x690")
ventana.configure(bg="#f8fafc")

encabezado = tk.Frame(ventana, bg="#0f172a", pady=5)
encabezado.pack(fill=tk.X)
tk.Label(encabezado, text="COMPUMEP | GESTIÓN DE LABORATORIO Y SERVICIOS", 
         font=("Segoe UI", 11, "bold"), fg="#f8fafc", bg="#0f172a").pack()

panel_principal = tk.Frame(ventana, bg="#f8fafc", padx=10, pady=5)
panel_principal.pack(fill=tk.BOTH, expand=True)

# LADO IZQUIERDO: FORMULARIO
frame_form = tk.LabelFrame(panel_principal, text=" Ficha Técnica Operativa ", font=("Segoe UI", 9, "bold"), bg="#f8fafc", padx=10, pady=5)
frame_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

# Fila 0: Orden + Urgencia
tk.Label(frame_form, text="N° Orden:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=0, column=0, sticky="w")
f_ord = tk.Frame(frame_form, bg="#f8fafc")
f_ord.grid(row=0, column=1, sticky="w", pady=2)
txt_orden = ttk.Entry(f_ord, width=12)
txt_orden.pack(side=tk.LEFT, padx=(0, 4))
btn_buscar = tk.Button(f_ord, text="🔍 Buscar", font=("Segoe UI", 8, "bold"), bg="#e2e8f0", command=buscar_orden)
btn_buscar.pack(side=tk.LEFT)

tk.Label(frame_form, text="Urgencia / Prioridad:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=0, column=2, sticky="w", padx=(10, 0))
cmb_urgencia = ttk.Combobox(frame_form, values=["Estándar (Turno regular)", "Prioridad Media", "Alta / Urgente (Mismo día)"], state="readonly", width=25)
cmb_urgencia.current(0)
cmb_urgencia.grid(row=0, column=3, sticky="w", pady=2)

# Fila 1: Dispositivo + Serial
tk.Label(frame_form, text="Tipo Dispositivo:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=1, column=0, sticky="w")
cmb_tipo = ttk.Combobox(frame_form, values=["Portátil", "Torre PC", "Todo en Uno (AIO)", "Impresora / UPS"], state="readonly", width=18)
cmb_tipo.current(0)
cmb_tipo.grid(row=1, column=1, sticky="w", pady=2)

tk.Label(frame_form, text="Serial / S/N:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=1, column=2, sticky="w", padx=(10, 0))
txt_serial = ttk.Entry(frame_form, width=27)
txt_serial.insert(0, "N/A")
txt_serial.grid(row=1, column=3, sticky="w", pady=2)

# Fila 2: Marca y Modelo
tk.Label(frame_form, text="Marca:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=2, column=0, sticky="w")
txt_marca = ttk.Entry(frame_form, width=20)
txt_marca.grid(row=2, column=1, sticky="w", pady=2)

tk.Label(frame_form, text="Modelo:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=2, column=2, sticky="w", padx=(10, 0))
txt_modelo = ttk.Entry(frame_form, width=27)
txt_modelo.grid(row=2, column=3, sticky="w", pady=2)

# Fila 3: Estado Físico
tk.Label(frame_form, text="Estado Físico / Bisagras:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=3, column=0, sticky="w")
txt_estado_fisico = ttk.Entry(frame_form, width=60)
txt_estado_fisico.insert(0, "Sin daños visibles aparentes")
txt_estado_fisico.grid(row=3, column=1, columnspan=3, sticky="we", pady=2)

# Fila 4: Voz del Cliente
tk.Label(frame_form, text="Falla Reportada (Cliente):", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=4, column=0, sticky="nw")
txt_falla_cliente = tk.Text(frame_form, height=2, width=60, font=("Segoe UI", 9))
txt_falla_cliente.grid(row=4, column=1, columnspan=3, sticky="we", pady=2)

# Fila 5: Telemetría SMART
tk.Label(frame_form, text="Telemetría SMART:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=5, column=0, sticky="w")
cmb_smart = ttk.Combobox(frame_form, values=[
    "Bueno (100% / Normal)",
    "Riesgo / Alerta (Sectores)",
    "Malo (Fallo inminente)",
    "No Aplica / Sin disco / Pendiente"
], state="readonly", width=30)
cmb_smart.current(0)
cmb_smart.grid(row=5, column=1, sticky="w", pady=2)

# Fila 6: Prediagnóstico Inicial (Mesa)
tk.Label(frame_form, text="Prediagnóstico (Mesa):", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=6, column=0, sticky="nw")
txt_prediagnostico = tk.Text(frame_form, height=2, width=60, font=("Segoe UI", 9))
txt_prediagnostico.grid(row=6, column=1, columnspan=3, sticky="we", pady=2)

# Fila 7: Catálogo + Semáforo + Agregar
tk.Label(frame_form, text="Catálogo Servicios:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=7, column=0, sticky="w")
cmb_servicio = ttk.Combobox(frame_form, values=list(CATALOGO_SERVICIOS.keys()), state="readonly", width=42)
if CATALOGO_SERVICIOS:
    cmb_servicio.current(0)
cmb_servicio.grid(row=7, column=1, columnspan=2, sticky="w", pady=2)

btn_agregar_serv = tk.Button(frame_form, text="+ Agregar", font=("Segoe UI", 8, "bold"), bg="#10b981", fg="white", command=agregar_servicio_a_lista)
btn_agregar_serv.grid(row=7, column=3, sticky="w", padx=(5, 0))

lbl_info_semaforo = tk.Label(frame_form, text="Semáforo: --", font=("Segoe UI", 8, "bold"), bg="#e2e8f0", padx=6, pady=2)
lbl_info_semaforo.grid(row=8, column=1, columnspan=3, sticky="we", pady=2)

def actualizar_semaforo(event=None):
    serv = cmb_servicio.get()
    if serv in CATALOGO_SERVICIOS:
        info = CATALOGO_SERVICIOS[serv]
        color = "#15803d" if info["semaforo"] == "Verde" else "#b45309" if info["semaforo"] == "Amarillo" else "#b91c1c"
        lbl_info_semaforo.config(text=f"Nivel: {info['semaforo']} | Estimado: {info['tiempo']}", fg=color)

cmb_servicio.bind("<<ComboboxSelected>>", actualizar_semaforo)
actualizar_semaforo()

# Fila 9: Lista de Servicios Asignados
tk.Label(frame_form, text="Servicios Aplicados:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=9, column=0, sticky="nw")
f_lst = tk.Frame(frame_form, bg="#f8fafc")
f_lst.grid(row=9, column=1, columnspan=3, sticky="we", pady=2)

lst_servicios = tk.Listbox(f_lst, height=5, font=("Segoe UI", 8))
lst_servicios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
btn_quitar_serv = tk.Button(f_lst, text="Quitar", font=("Segoe UI", 7), bg="#ef4444", fg="white", command=quitar_servicio_de_lista)
btn_quitar_serv.pack(side=tk.LEFT, padx=(5, 0))

# Fila 10: Diagnóstico Técnico Definitivo
tk.Label(frame_form, text="Diagnóstico Definitivo:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=10, column=0, sticky="nw")
txt_diagnostico = tk.Text(frame_form, height=2, width=60, font=("Segoe UI", 9))
txt_diagnostico.grid(row=10, column=1, columnspan=3, sticky="we", pady=2)

# Fila 11: Solución Realizada
tk.Label(frame_form, text="Solución Técnica:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=11, column=0, sticky="nw")
txt_solucion = tk.Text(frame_form, height=5, width=60, font=("Segoe UI", 9))
txt_solucion.grid(row=11, column=1, columnspan=3, sticky="we", pady=2)

# Fila 12: Observaciones y Salvedades de Garantía
tk.Label(frame_form, text="Salvedades / Garantía:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=12, column=0, sticky="nw")
txt_observaciones = tk.Text(frame_form, height=2, width=60, font=("Segoe UI", 9))
txt_observaciones.grid(row=12, column=1, columnspan=3, sticky="we", pady=2)

# Fila 13: Estado de la Orden
tk.Label(frame_form, text="Estado de la Orden:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").grid(row=13, column=0, sticky="w")
cmb_estado_orden = ttk.Combobox(frame_form, values=[
    "En mesa (Descarte básico)",
    "En reposo / Prueba 24h",
    "Requiere laboratorio especializado (Electrónica)",
    "Esperando aprobación cliente",
    "En reparación / Mantenimiento",
    "Listo para entrega / Entregado"
], state="readonly", width=35)
cmb_estado_orden.current(0)
cmb_estado_orden.grid(row=13, column=1, columnspan=2, sticky="w", pady=2)

# Botones inferiores del formulario
f_btns = tk.Frame(frame_form, bg="#f8fafc")
f_btns.grid(row=14, column=0, columnspan=4, sticky="we", pady=(6, 0))

btn_guardar = tk.Button(f_btns, text="GUARDAR / ACTUALIZAR", bg="#0284c7", fg="white", font=("Segoe UI", 9, "bold"), pady=4, cursor="hand2", command=guardar_o_actualizar_ficha)
btn_guardar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

btn_copiar = tk.Button(f_btns, text="📋 Copiar para Web", bg="#8b5cf6", fg="white", font=("Segoe UI", 9, "bold"), pady=4, cursor="hand2", command=copiar_reporte_web)
btn_copiar.pack(side=tk.LEFT, padx=(0, 4))

btn_limpiar = tk.Button(f_btns, text="Limpiar", bg="#64748b", fg="white", font=("Segoe UI", 9), pady=4, cursor="hand2", command=limpiar_formulario)
btn_limpiar.pack(side=tk.RIGHT)

# LADO DERECHO: MONITOR EN VIVO
frame_monitor = tk.LabelFrame(panel_principal, text=" Taller en Vivo (Doble clic para cargar) ", font=("Segoe UI", 9, "bold"), bg="#f8fafc", padx=8, pady=5)
frame_monitor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

columnas = ("orden", "urgencia", "equipo", "semaforo", "estado")
tree_ordenes = ttk.Treeview(frame_monitor, columns=columnas, show="headings", height=24)

tree_ordenes.heading("orden", text="N° Orden")
tree_ordenes.heading("urgencia", text="Urgencia")
tree_ordenes.heading("equipo", text="Dispositivo")
tree_ordenes.heading("semaforo", text="Semáforo")
tree_ordenes.heading("estado", text="Estado")

tree_ordenes.column("orden", width=65, anchor="center")
tree_ordenes.column("urgencia", width=95, anchor="center")
tree_ordenes.column("equipo", width=120)
tree_ordenes.column("semaforo", width=75, anchor="center")
tree_ordenes.column("estado", width=110)

scroll_y = ttk.Scrollbar(frame_monitor, orient=tk.VERTICAL, command=tree_ordenes.yview)
tree_ordenes.configure(yscrollcommand=scroll_y.set)

tree_ordenes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

tree_ordenes.bind("<Double-1>", al_hacer_doble_clic)

cargar_tabla_monitoreo()

if __name__ == "__main__":
    ventana.mainloop()