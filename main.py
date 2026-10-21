import flet as ft
import backend  # Capa de lógica y base de datos (MySQL)

# =====================================================================
# ROL: DESARROLLADOR FRONTEND (INTERFAZ EN FLET)
# Propósito de este archivo:
# Gestionar la interfaz de usuario del taller Compumep. No contiene
# consultas SQL ni manejo de archivos directos; consume backend.py.
# =====================================================================

def main(page: ft.Page):
    # ---------------------------------------------------------
    # 1. CONFIGURACIÓN DE LA VENTANA PRINCIPAL
    # ---------------------------------------------------------
    page.title = "Compumep - Sistema de Control y Trazabilidad de Laboratorio (MVP)"
    page.window_width = 1280
    page.window_height = 760
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f8fafc"
    page.padding = 15

    # Memoria local para la sesión activa
    catalogo_actual = backend.cargar_catalogo_db()
    servicios_seleccionados = []

    def mostrar_mensaje(texto, color="#0f172a"):
        page.snack_bar = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # ---------------------------------------------------------
    # 2. CAMPOS DEL FORMULARIO OPERATIVO (LADO IZQUIERDO)
    # ---------------------------------------------------------
    txt_orden = ft.TextField(
        label="N° Orden",
        width=130,
        height=45,
        text_size=13,
        capitalization=ft.TextCapitalization.CHARACTERS
    )

    cmb_urgencia = ft.Dropdown(
        label="Urgencia / Prioridad",
        width=230,
        text_size=13,
        options=[
            ft.dropdown.Option("Estándar (Turno regular)"),
            ft.dropdown.Option("Prioridad Media"),
            ft.dropdown.Option("Alta / Urgente (Mismo día)"),
        ],
        value="Estándar (Turno regular)"
    )

    cmb_tipo = ft.Dropdown(
        label="Tipo Dispositivo",
        width=180,
        text_size=13,
        options=[
            ft.dropdown.Option("Portátil"),
            ft.dropdown.Option("Torre PC"),
            ft.dropdown.Option("Todo en Uno (AIO)"),
            ft.dropdown.Option("Impresora / UPS"),
        ],
        value="Portátil"
    )

    txt_serial = ft.TextField(label="Serial / S/N", value="N/A", width=180, height=45, text_size=13)
    txt_marca = ft.TextField(label="Marca", width=180, height=45, text_size=13)
    txt_modelo = ft.TextField(label="Modelo", width=180, height=45, text_size=13)

    txt_estado_fisico = ft.TextField(
        label="Estado Físico de Entrada (Carcasa / Bisagras / Tornillos)",
        value="Sin daños visibles aparentes",
        text_size=13
    )

    txt_falla_cliente = ft.TextField(
        label="Falla Reportada por el Cliente",
        multiline=True,
        min_lines=2,
        max_lines=2,
        text_size=13
    )

    cmb_smart = ft.Dropdown(
        label="Telemetría S.M.A.R.T. (Disco)",
        width=280,
        text_size=13,
        options=[
            ft.dropdown.Option("Bueno (100% / Normal)"),
            ft.dropdown.Option("Riesgo / Alerta (Sectores)"),
            ft.dropdown.Option("Malo (Fallo inminente)"),
            ft.dropdown.Option("No Aplica / Sin disco / Pendiente"),
        ],
        value="Bueno (100% / Normal)"
    )

    cmb_estado_orden = ft.Dropdown(
        label="Estado Operativo de la Orden",
        width=280,
        text_size=13,
        options=[
            ft.dropdown.Option("En mesa (Descarte básico)"),
            ft.dropdown.Option("En reposo / Prueba 24h"),
            ft.dropdown.Option("Requiere laboratorio especializado (Electrónica)"),
            ft.dropdown.Option("Esperando aprobación cliente"),
            ft.dropdown.Option("En reparación / Mantenimiento"),
            ft.dropdown.Option("Listo para entrega / Entregado"),
        ],
        value="En mesa (Descarte básico)"
    )

    txt_prediagnostico = ft.TextField(
        label="Prediagnóstico Inicial en Mesa (10-15 min)",
        multiline=True,
        min_lines=2,
        max_lines=2,
        text_size=13
    )

    txt_diagnostico = ft.TextField(
        label="Diagnóstico Técnico Definitivo (Causa Raíz)",
        multiline=True,
        min_lines=2,
        max_lines=2,
        text_size=13
    )

    txt_solucion = ft.TextField(
        label="Solución / Trabajo Técnico Realizado",
        multiline=True,
        min_lines=3,
        max_lines=3,
        text_size=13
    )

    txt_observaciones = ft.TextField(
        label="Observaciones y Salvedades de Garantía",
        multiline=True,
        min_lines=2,
        max_lines=2,
        text_size=13
    )

    # ---------------------------------------------------------
    # 3. GESTIÓN DEL CATÁLOGO DINÁMICO DE SERVICIOS
    # ---------------------------------------------------------
    cmb_servicio = ft.Dropdown(
        label="Seleccionar Servicio del Catálogo",
        width=320,
        text_size=13,
        options=[ft.dropdown.Option(nombre) for nombre in catalogo_actual.keys()]
    )

    txt_nuevo_servicio = ft.TextField(
        label="O escribir servicio nuevo...",
        width=220,
        height=45,
        text_size=12
    )

    contenedor_chips_servicios = ft.Row(wrap=True, spacing=6, run_spacing=6)

    def actualizar_vista_servicios():
        contenedor_chips_servicios.controls.clear()
        for serv in servicios_seleccionados:
            def quitar_serv(e, nombre=serv):
                servicios_seleccionados.remove(nombre)
                actualizar_vista_servicios()

            chip = ft.Chip(
                label=ft.Text(serv, size=12),
                on_delete=quitar_serv,
                bgcolor="#e0f2fe"
            )
            contenedor_chips_servicios.controls.append(chip)
        page.update()

    def agregar_servicio_evento(e):
        nonlocal catalogo_actual
        servicio_escrito = txt_nuevo_servicio.value.strip() if txt_nuevo_servicio.value else ""
        servicio_elegido = cmb_servicio.value

        if servicio_escrito:
            nombre_final = servicio_escrito
            if nombre_final not in catalogo_actual:
                nuevo_id = backend.agregar_nuevo_servicio_db(nombre_final)
                catalogo_actual[nombre_final] = nuevo_id
                cmb_servicio.options.append(ft.dropdown.Option(nombre_final))
                mostrar_mensaje(f"Nuevo servicio '{nombre_final}' aprendido en BD.", "#0284c7")
            txt_nuevo_servicio.value = ""
        elif servicio_elegido:
            nombre_final = servicio_elegido
        else:
            mostrar_mensaje("Seleccione un servicio o escriba uno nuevo.", "#d97706")
            return

        if nombre_final in servicios_seleccionados:
            mostrar_mensaje("Este servicio ya está asignado a la orden.", "#64748b")
            return

        servicios_seleccionados.append(nombre_final)
        actualizar_vista_servicios()

    # ---------------------------------------------------------
    # 4. ACCIONES DEL FORMULARIO (INTERACCIÓN CON BACKEND)
    # ---------------------------------------------------------
    def recolectar_datos_formulario():
        return {
            "orden": txt_orden.value.strip().upper() if txt_orden.value else "",
            "urgencia": cmb_urgencia.value,
            "tipo": cmb_tipo.value,
            "marca": txt_marca.value.strip() if txt_marca.value else "",
            "modelo": txt_modelo.value.strip() if txt_modelo.value else "",
            "serial": txt_serial.value.strip() if txt_serial.value else "N/A",
            "est_fisico": txt_estado_fisico.value.strip() if txt_estado_fisico.value else "Sin daños visibles aparentes",
            "falla_cli": txt_falla_cliente.value.strip() if txt_falla_cliente.value else "",
            "smart": cmb_smart.value,
            "estado_orden": cmb_estado_orden.value,
            "prediag": txt_prediagnostico.value.strip() if txt_prediagnostico.value else "",
            "diag": txt_diagnostico.value.strip() if txt_diagnostico.value else "",
            "solucion": txt_solucion.value.strip() if txt_solucion.value else "",
            "obs": txt_observaciones.value.strip() if txt_observaciones.value else ""
        }

    def limpiar_formulario_evento(e=None):
        txt_orden.value = ""
        cmb_urgencia.value = "Estándar (Turno regular)"
        cmb_tipo.value = "Portátil"
        txt_serial.value = "N/A"
        txt_marca.value = ""
        txt_modelo.value = ""
        txt_estado_fisico.value = "Sin daños visibles aparentes"
        txt_falla_cliente.value = ""
        cmb_smart.value = "Bueno (100% / Normal)"
        cmb_estado_orden.value = "En mesa (Descarte básico)"
        txt_prediagnostico.value = ""
        txt_diagnostico.value = ""
        txt_solucion.value = ""
        txt_observaciones.value = ""
        txt_nuevo_servicio.value = ""
        servicios_seleccionados.clear()
        actualizar_vista_servicios()
        page.update()

    def buscar_orden_evento(e=None):
        orden = txt_orden.value.strip().upper() if txt_orden.value else ""
        if not orden:
            mostrar_mensaje("Ingrese un número de orden para buscar.", "#d97706")
            return

        registro, servs = backend.buscar_orden_db(orden)
        if not registro:
            mostrar_mensaje(f"La orden {orden} no existe en la base de datos.", "#dc2626")
            return

        cmb_tipo.value = registro["tipo_equipo"]
        txt_marca.value = registro["marca"]
        txt_modelo.value = registro["modelo"]
        txt_serial.value = registro["serial"]
        txt_estado_fisico.value = registro["estado_fisico"]
        txt_falla_cliente.value = registro["falla_cliente"]
        cmb_urgencia.value = registro["urgencia"] or "Estándar (Turno regular)"
        cmb_estado_orden.value = registro["estado"] or "En mesa (Descarte básico)"
        cmb_smart.value = registro["salud_smart"] or "Bueno (100% / Normal)"
        txt_prediagnostico.value = registro["prediagnostico_inicial"] or ""
        txt_diagnostico.value = registro["diagnostico_definitivo"] or ""
        txt_solucion.value = registro["solucion_tecnica"] or ""
        txt_observaciones.value = registro["observaciones_garantia"] or ""

        servicios_seleccionados.clear()
        servicios_seleccionados.extend(servs)
        actualizar_vista_servicios()
        mostrar_mensaje(f"Orden {orden} cargada con éxito.", "#15803d")

    def guardar_ficha_evento(e):
        datos = recolectar_datos_formulario()
        if not datos["orden"] or not datos["marca"] or not datos["modelo"] or not datos["falla_cli"]:
            mostrar_mensaje("Campos requeridos: N° Orden, Marca, Modelo y Falla.", "#dc2626")
            return

        try:
            accion, fecha = backend.guardar_o_actualizar_db(datos, servicios_seleccionados, catalogo_actual)
            ruta_txt = backend.generar_archivo_ficha_txt(datos, servicios_seleccionados, fecha)
            
            limpiar_formulario_evento()
            cargar_tabla_monitoreo()  # Recarga la lista lateral al instante
            mostrar_mensaje(f"✓ Orden {datos['orden']} {accion} correctamente.", "#15803d")
        except Exception as err:
            mostrar_mensaje(f"Error al guardar: {err}", "#dc2626")

    def copiar_web_evento(e):
        datos = recolectar_datos_formulario()
        if not datos["orden"]:
            mostrar_mensaje("Ingrese o cargue una orden antes de copiar.", "#d97706")
            return
        resumen = backend.construir_resumen_web(datos, servicios_seleccionados)
        page.set_clipboard(resumen)
        mostrar_mensaje("📋 Reporte copiado. Listo para pegar (Ctrl+V) en el sistema web.", "#7c3aed")

    # ---------------------------------------------------------
    # 5. PANEL DE MONITOREO EN VIVO (LADO DERECHO)
    # ---------------------------------------------------------
    tabla_ordenes = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Orden", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Urgencia", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Equipo", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        heading_row_color="#e2e8f0",
        column_spacing=18,
    )

    def cargar_tabla_monitoreo():
        tabla_ordenes.rows.clear()
        try:
            registros = backend.obtener_ordenes_activas_db()
            for reg in registros:
                oid = str(reg["id_orden"])
                urg = str(reg.get("urgencia") or "Estándar")
                eq = str(reg.get("equipo") or "N/A")
                est = str(reg.get("estado") or "En proceso")

                def seleccionar_orden(e, id_a_cargar=oid):
                    txt_orden.value = id_a_cargar
                    buscar_orden_evento()

                fila = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(oid, weight=ft.FontWeight.BOLD, color="#0284c7"), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(urg, size=12), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(eq, size=12), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(est, size=12), on_tap=seleccionar_orden),
                    ]
                )
                tabla_ordenes.rows.append(fila)

            tabla_ordenes.update()
            page.update()
        except Exception as err:
            print(f"Error cargando tabla: {err}")

    # ---------------------------------------------------------
    # 6. DISTRIBUCIÓN VISUAL DE LA INTERFAZ (LAYOUT)
    # ---------------------------------------------------------
    encabezado = ft.Container(
        content=ft.Text(
            "COMPUMEP | GESTIÓN DE LABORATORIO Y ESTANDARIZACIÓN DE SERVICIOS (MVP)",
            size=16,
            weight=ft.FontWeight.BOLD,
            color="white"
        ),
        bgcolor="#0f172a",
        padding=12,
        border_radius=8
    )

    panel_izquierdo = ft.Container(
        expand=3,
        bgcolor="white",
        padding=15,
        border_radius=8,
        border=ft.Border.all(1, "#cbd5e1"),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                ft.Text("Ficha Técnica Operativa", size=15, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Row([
                    txt_orden,
                    ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=buscar_orden_evento),
                    cmb_urgencia
                ]),
                ft.Row([cmb_tipo, txt_marca, txt_modelo, txt_serial]),
                txt_estado_fisico,
                txt_falla_cliente,
                ft.Row([cmb_smart, cmb_estado_orden]),
                txt_prediagnostico,
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Text("Servicios Aplicados (Catálogo Dinámico)", size=13, weight=ft.FontWeight.BOLD),
                ft.Row([
                    cmb_servicio,
                    txt_nuevo_servicio,
                    ft.Button("+ Agregar", bgcolor="#10b981", color="white", on_click=agregar_servicio_evento)
                ]),
                contenedor_chips_servicios,
                ft.Divider(height=1, color="#e2e8f0"),
                txt_diagnostico,
                txt_solucion,
                txt_observaciones,
                ft.Row([
                    ft.Button("GUARDAR / ACTUALIZAR", icon=ft.Icons.SAVE, bgcolor="#0284c7", color="white", expand=True, on_click=guardar_ficha_evento),
                    ft.Button("Copiar para Web", icon=ft.Icons.COPY, bgcolor="#7c3aed", color="white", on_click=copiar_web_evento),
                    ft.OutlinedButton("Limpiar", on_click=limpiar_formulario_evento),
                ])
            ]
        )
    )

    panel_derecho = ft.Container(
        expand=2,
        bgcolor="white",
        padding=15,
        border_radius=8,
        border=ft.Border.all(1, "#cbd5e1"),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Equipos Activos en Taller", size=15, weight=ft.FontWeight.BOLD, color="#0f172a"),
                tabla_ordenes
            ]
        )
    )

    # 1. Montamos primero la estructura visual en la página
    page.add(
        encabezado,
        ft.Row([panel_izquierdo, panel_derecho], expand=True, spacing=15)
    )

    # 2. Carga automática inicial de datos una vez los controles existen en pantalla
    cargar_tabla_monitoreo()

# ---------------------------------------------------------
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ---------------------------------------------------------
if __name__ == "__main__":
    ft.run(main)