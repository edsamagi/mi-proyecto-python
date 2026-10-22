import flet as ft
import backend  # Conexión directa a MySQL y lógica de negocio

# =====================================================================
# ROL: DESARROLLADOR FRONTEND / INTERFAZ EN FLET
# Ajustes de legibilidad:
# - Jerarquía visual clara: labels en gris técnico (#64748b) y texto en carbón nítido (#0f172a)
# - Diferenciación entre títulos de casillas y contenido redactado
# =====================================================================

def main(page: ft.Page):
    page.title = "Compumep - Sistema de Control y Trazabilidad de Laboratorio (MVP)"
    page.window_width = 1490
    page.window_height = 740
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f1f5f9"
    page.padding = 12

    clipboard = ft.Clipboard()
    page.services.append(clipboard)

    catalogo_actual = backend.cargar_catalogo_db()
    servicios_seleccionados = []

    def mostrar_mensaje(texto, color="#0f172a"):
        page.show_dialog(ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color))

    def estilo_boton(base, hover, presionado):
        return ft.ButtonStyle(
            bgcolor={
                ft.ControlState.PRESSED: presionado,
                ft.ControlState.HOVERED: hover,
                ft.ControlState.DEFAULT: base,
            },
            color="white",
            animation_duration=150,
        )

    # Estilos compartidos para crear jerarquía visual clara
    estilo_label = ft.TextStyle(size=11, color="#64748b", weight=ft.FontWeight.W_500)
    estilo_texto = ft.TextStyle(size=13, color="#0f172a")

    # =====================================================================
    # SECCIÓN 1: CONTROLES - ENTRADA Y PREDIAGNÓSTICO (COLUMNA 1)
    # =====================================================================
    txt_orden = ft.TextField(
        label="N° Orden",
        width=120,
        height=45,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        capitalization=ft.TextCapitalization.CHARACTERS
    )

    cmb_urgencia = ft.Dropdown(
        label="Urgencia / Prioridad",
        expand=True,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        options=[
            ft.dropdown.Option("Estándar (Turno regular)"),
            ft.dropdown.Option("Prioridad Media"),
            ft.dropdown.Option("Alta / Urgente (Mismo día)"),
        ],
        value="Estándar (Turno regular)"
    )

    cmb_tipo = ft.Dropdown(
        label="Tipo",
        width=120,
        text_style=ft.TextStyle(size=12, color="#0f172a"),
        label_style=estilo_label,
        border_color="#cbd5e1",
        options=[
            ft.dropdown.Option("Portátil"),
            ft.dropdown.Option("Torre PC"),
            ft.dropdown.Option("Todo en Uno"),
            ft.dropdown.Option("Otros"),
        ],
        value="Portátil"
    )

    txt_marca = ft.TextField(
        label="Marca", 
        expand=2, 
        height=45, 
        text_style=estilo_texto, 
        label_style=estilo_label, 
        border_color="#cbd5e1"
    )
    
    txt_modelo = ft.TextField(
        label="Modelo", 
        expand=2, 
        height=45, 
        text_style=estilo_texto, 
        label_style=estilo_label, 
        border_color="#cbd5e1"
    )
    
    txt_serial = ft.TextField(
        label="Serial / S/N", 
        value="N/A", 
        expand=2, 
        height=45, 
        text_style=estilo_texto, 
        label_style=estilo_label, 
        border_color="#cbd5e1"
    )

    txt_falla_cliente = ft.TextField(
        label="Falla Reportada por el Cliente",
        multiline=True,
        min_lines=5,
        max_lines=6,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        expand=True,
        align_label_with_hint=True
    )

    txt_estado_fisico = ft.TextField(
        label="Estado Físico (Carcasa / Bisagras)",
        value="Sin daños visibles aparentes",
        expand=3,
        height=48,
        text_style=ft.TextStyle(size=12, color="#0f172a"),
        label_style=estilo_label,
        border_color="#cbd5e1"
    )

    cmb_smart = ft.Dropdown(
        label="Telemetría S.M.A.R.T.",
        expand=2,
        text_style=ft.TextStyle(size=12, color="#0f172a"),
        label_style=estilo_label,
        border_color="#cbd5e1",
        options=[
            ft.dropdown.Option("Bueno (100% / Normal)"),
            ft.dropdown.Option("Riesgo / Alerta (Sectores)"),
            ft.dropdown.Option("Malo (Fallo inminente)"),
            ft.dropdown.Option("No Aplica / Sin disco"),
        ],
        value="Bueno (100% / Normal)"
    )

    txt_prediagnostico = ft.TextField(
        label="Prediagnóstico Inicial en Mesa (10-15 min)",
        multiline=True,
        min_lines=5,
        max_lines=6,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        expand=True,
        align_label_with_hint=True
    )

    cmb_estado_orden = ft.Dropdown(
        label="Estado Operativo de la Orden",
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
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

    # =====================================================================
    # SECCIÓN 2: CONTROLES - SERVICIOS Y DIAGNÓSTICO (COLUMNA 2)
    # =====================================================================
    cmb_servicio = ft.Dropdown(
        label="Seleccionar Servicio del Catálogo",
        expand=3,
        text_style=ft.TextStyle(size=12, color="#0f172a"),
        label_style=estilo_label,
        border_color="#cbd5e1",
        options=[ft.dropdown.Option(nombre) for nombre in catalogo_actual.keys()]
    )

    txt_nuevo_servicio = ft.TextField(
        label="Escribir servicio nuevo...",
        expand=2,
        height=45,
        text_style=ft.TextStyle(size=12, color="#0f172a"),
        label_style=estilo_label,
        border_color="#cbd5e1"
    )

    contenedor_chips_servicios = ft.Row(wrap=True, spacing=6, run_spacing=6)

    def actualizar_vista_servicios():
        contenedor_chips_servicios.controls.clear()
        for serv in servicios_seleccionados:
            def quitar_serv(e, nombre=serv):
                servicios_seleccionados.remove(nombre)
                actualizar_vista_servicios()

            chip = ft.Chip(
                label=ft.Text(serv, size=11, color="#0369a1"),
                on_delete=quitar_serv,
                bgcolor="#f0f9ff"
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
                mostrar_mensaje(f"Servicio '{nombre_final}' guardado en BD.", "#0284c7")
            txt_nuevo_servicio.value = ""
        elif servicio_elegido:
            nombre_final = servicio_elegido
        else:
            mostrar_mensaje("Seleccione un servicio o escriba uno nuevo.", "#d97706")
            return

        if nombre_final in servicios_seleccionados:
            mostrar_mensaje("Este servicio ya está en la lista.", "#64748b")
            return

        servicios_seleccionados.append(nombre_final)
        actualizar_vista_servicios()

    txt_diagnostico = ft.TextField(
        label="Diagnóstico Técnico Definitivo (Causa Raíz)",
        multiline=True,
        min_lines=3,
        max_lines=4,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        expand=True,
        align_label_with_hint=True
    )

    txt_solucion = ft.TextField(
        label="Proceso / Solución / Trabajo Técnico Realizado",
        multiline=True,
        min_lines=3,
        max_lines=4,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        expand=True,
        align_label_with_hint=True
    )

    txt_observaciones = ft.TextField(
        label="Observaciones y Salvedades de Garantía",
        multiline=True,
        min_lines=3,
        max_lines=4,
        text_style=estilo_texto,
        label_style=estilo_label,
        border_color="#cbd5e1",
        expand=True,
        align_label_with_hint=True
    )

    # =====================================================================
    # SECCIÓN 3: ACCIONES DE NEGOCIO Y PERSISTENCIA
    # =====================================================================
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
            mostrar_mensaje("Ingrese una orden para buscar.", "#d97706")
            return

        registro, servs = backend.buscar_orden_db(orden)
        if not registro:
            mostrar_mensaje(f"La orden {orden} no existe en MySQL.", "#dc2626")
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
            mostrar_mensaje("Faltan campos clave: Orden, Marca, Modelo o Falla.", "#dc2626")
            return

        try:
            accion, fecha = backend.guardar_o_actualizar_db(datos, servicios_seleccionados, catalogo_actual)
            ruta_csv = backend.generar_archivo_ficha_csv(datos, servicios_seleccionados, fecha)
            limpiar_formulario_evento()
            cargar_tabla_monitoreo()
            mostrar_mensaje(f"✓ Orden {datos['orden']} {accion}. Registro CSV: {ruta_csv}", "#15803d")
        except Exception as err:
            mostrar_mensaje(f"Error al guardar: {err}", "#dc2626")

    async def copiar_web_evento(e):
        datos = recolectar_datos_formulario()
        if not datos["orden"]:
            mostrar_mensaje("Cargue una orden para copiar el reporte.", "#d97706")
            return
        resumen = backend.construir_resumen_web(datos, servicios_seleccionados)
        await clipboard.set(resumen)
        mostrar_mensaje("📋 Reporte técnico copiado al portapapeles (Ctrl+V).", "#7c3aed")

    # =====================================================================
    # SECCIÓN 4: MONITOR DE ÓRDENES ACTIVAS
    # =====================================================================
    tabla_ordenes = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Orden", weight=ft.FontWeight.BOLD, size=11, color="#475569")),
            ft.DataColumn(ft.Text("Urgencia", weight=ft.FontWeight.BOLD, size=11, color="#475569")),
            ft.DataColumn(ft.Text("Equipo", weight=ft.FontWeight.BOLD, size=11, color="#475569")),
            ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=11, color="#475569")),
        ],
        rows=[],
        heading_row_color="#f8fafc",
        column_spacing=10,
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
                        ft.DataCell(ft.Text(oid, weight=ft.FontWeight.BOLD, color="#0284c7", size=11), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(urg, size=11, color="#334155"), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(eq, size=11, color="#334155"), on_tap=seleccionar_orden),
                        ft.DataCell(ft.Text(est, size=11, color="#334155"), on_tap=seleccionar_orden),
                    ]
                )
                tabla_ordenes.rows.append(fila)

            tabla_ordenes.update()
            page.update()
        except Exception as err:
            print(f"Error cargando tabla: {err}")

    # =====================================================================
    # SECCIÓN 5: MAQUETACIÓN VISUAL
    # =====================================================================
    panel_prediagnostico = ft.Container(
        expand=4,
        bgcolor="white",
        padding=14,
        border_radius=8,
        border=ft.Border.all(1, "#e2e8f0"),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                ft.Text("Ficha Técnica - Recepción y Filtro de Mesa", size=14, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Row([
                    txt_orden,
                    ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=buscar_orden_evento),
                    cmb_urgencia
                ]),
                ft.Row([cmb_tipo, txt_marca, txt_modelo, txt_serial], spacing=6),
                ft.Row([txt_falla_cliente]),
                ft.Row([txt_estado_fisico, cmb_smart], spacing=8),
                ft.Row([txt_prediagnostico]),
                cmb_estado_orden,
            ]
        )
    )

    panel_servicios_diagnostico = ft.Container(
        expand=4,
        bgcolor="white",
        padding=14,
        border_radius=8,
        border=ft.Border.all(1, "#e2e8f0"),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                ft.Text("Laboratorio Técnico - Servicios y Solución", size=14, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Row([
                    cmb_servicio,
                    txt_nuevo_servicio,
                    ft.Button("+ Agregar", style=estilo_boton("#10b981", "#059669", "#047857"), on_click=agregar_servicio_evento)
                ]),
                contenedor_chips_servicios,
                ft.Row([txt_diagnostico]),
                ft.Row([txt_solucion]),
                ft.Row([txt_observaciones]),
                ft.Row([
                    ft.Button("GUARDAR / ACTUALIZAR", icon=ft.Icons.SAVE, style=estilo_boton("#0284c7", "#0369a1", "#075985"), expand=True, on_click=guardar_ficha_evento),
                    ft.Button("Copiar Web", icon=ft.Icons.COPY, style=estilo_boton("#7c3aed", "#6d28d9", "#5b21b6"), on_click=copiar_web_evento),
                    ft.OutlinedButton("Limpiar", on_click=limpiar_formulario_evento),
                ], spacing=6)
            ]
        )
    )

    panel_monitor = ft.Container(
        expand=3,
        bgcolor="white",
        padding=12,
        border_radius=8,
        border=ft.Border.all(1, "#e2e8f0"),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Órdenes en Taller (Clic para cargar)", size=13, weight=ft.FontWeight.BOLD, color="#0f172a"),
                tabla_ordenes
            ]
        )
    )

    page.add(
        ft.Row(
            [panel_prediagnostico, panel_servicios_diagnostico, panel_monitor],
            expand=True,
            spacing=10
        )
    )

    cargar_tabla_monitoreo()

if __name__ == "__main__":
    ft.run(main)