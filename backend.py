import os
from datetime import datetime
import mysql.connector

# =====================================================================
# ROL: DESARROLLADOR BACKEND EN PYTHON
# Propósito de este archivo:
# Actuar como el "cerebro" del software. Aquí se concentra toda la lógica
# interna: conexión a MySQL, búsqueda y guardado de órdenes, y creación
# de los reportes (.txt y portapapeles). No contiene nada visual (botones/ventanas).
# =====================================================================

# 1. PARÁMETROS DE CONEXIÓN A LA BASE DE DATOS LOCAL (MySQL)
# Se guardan en un diccionario para pasarlos fácilmente al conector.
DB_CONFIG = {
    "host": "localhost",       # El servidor está en el mismo computador del taller
    "port": 3306,              # Puerto estándar de MySQL
    "user": "root",            # Usuario administrador local
    "password": "123qwe",      # Contraseña configurada en MySQL
    "database": "compumep_db"  # Nombre de nuestra base de datos
}

def obtener_conexion():
    """
    Función puente: cada vez que el programa necesita hablar con MySQL,
    llama a esta función para abrir el canal de comunicación.
    """
    return mysql.connector.connect(**DB_CONFIG)


# =====================================================================
# 2. GESTIÓN DEL CATÁLOGO DE SERVICIOS (SIMPLIFICADO PARA EL MVP)
# =====================================================================

def cargar_catalogo_db():
    """
    Consulta todos los servicios guardados en la tabla 'catalogo_servicios'.
    Ya no trae el semáforo para mantener el MVP simple y directo.
    Devuelve un diccionario donde la clave es el nombre del servicio y el valor es su ID.
    Ejemplo: {'Reprogramación básica': 1, 'Cambio de pasta térmica': 2}
    """
    catalogo = {}
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Se ordenan alfabéticamente (ASC) para que sea más fácil encontrarlos en la lista
    cursor.execute("SELECT id_servicio, nombre_servicio FROM catalogo_servicios ORDER BY nombre_servicio ASC;")
    
    # Recorremos cada fila que devolvió MySQL y la guardamos en el diccionario
    for id_serv, nombre in cursor.fetchall():
        catalogo[nombre] = id_serv
        
    cursor.close()
    conexion.close()
    return catalogo


def agregar_nuevo_servicio_db(nombre_servicio):
    """
    Si en el taller realizas un trabajo nuevo que no existía en la lista,
    esta función lo guarda automáticamente en MySQL para que quede disponible
    para siempre sin tener que abrir MySQL Workbench.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Insertamos el nuevo nombre. En nivel_semaforo y tiempo_estimado ponemos valores
    # por defecto ('N/A', 'Estándar') para no romper la estructura original de tu tabla en MySQL.
    cursor.execute(
        "INSERT INTO catalogo_servicios (nombre_servicio, nivel_semaforo, tiempo_estimado) VALUES (%s, 'N/A', 'Estándar');",
        (nombre_servicio.strip(),)
    )
    
    # Capturamos el ID numérico que MySQL le asignó automáticamente a este nuevo servicio
    nuevo_id = cursor.lastrowid
    
    # commit() confirma y guarda los cambios de forma permanente en el disco duro
    conexion.commit()
    cursor.close()
    conexion.close()
    return nuevo_id


# =====================================================================
# 3. CONSULTAS DE ÓRDENES ACTIVAS Y BÚSQUEDA INDIVIDUAL
# =====================================================================

def obtener_ordenes_activas_db():
    """
    Busca todas las órdenes que siguen en el taller (que NO han sido entregadas)
    para mostrarlas en la tabla de monitoreo del lado derecho de la pantalla.
    """
    conexion = obtener_conexion()
    # dictionary=True hace que MySQL nos entregue los datos con el nombre de la columna
    # (ej: fila['id_orden']) en lugar de posiciones numéricas confusas (fila[0]).
    cursor = conexion.cursor(dictionary=True)
    
    # Unimos (JOIN) la tabla de órdenes con la de equipos para juntar marca y modelo.
    # El CASE en el ORDER BY pone primero las órdenes "Urgentes", luego "Media" y al final "Estándar".
    consulta = """
        SELECT 
            o.id_orden,
            o.urgencia,
            CONCAT(e.marca, ' ', e.modelo) AS equipo,
            o.estado
        FROM ORDENES_SERVICIO o
        JOIN EQUIPOS e ON o.id_equipo = e.id_equipo
        WHERE o.estado NOT LIKE '%Entregado%' 
          AND o.estado NOT LIKE '%Listo para entrega%'
        ORDER BY 
            CASE 
                WHEN o.urgencia LIKE '%Urgente%' THEN 1
                WHEN o.urgencia LIKE '%Media%' THEN 2
                ELSE 3
            END ASC,
            o.fecha_ingreso DESC;
    """
    cursor.execute(consulta)
    registros = cursor.fetchall()
    cursor.close()
    conexion.close()
    return registros


def buscar_orden_db(orden):
    """
    Cuando escribes un número de orden o le das clic en la tabla, esta función
    trae toda la historia clínica de esa máquina desde las tablas de MySQL.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # 1. Traemos los datos generales de la orden, del equipo y de su ficha técnica
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
    registro = cursor.fetchone() # fetchone() trae un único resultado (porque la orden es única)

    # 2. Si la orden existe y tiene ficha técnica, buscamos qué servicios se le han aplicado
    servicios_asociados = []
    if registro and registro["id_ficha"]:
        sql_servicios = """
            SELECT c.nombre_servicio 
            FROM DETALLE_SERVICIOS_FICHA d
            JOIN CATALOGO_SERVICIOS c ON d.id_servicio = c.id_servicio
            WHERE d.id_ficha = %s;
        """
        cursor.execute(sql_servicios, (registro["id_ficha"],))
        for f_serv in cursor.fetchall():
            servicios_asociados.append(f_serv["nombre_servicio"])

    cursor.close()
    conexion.close()
    # Devolvemos dos cosas: el diccionario con los datos de la máquina y la lista de servicios
    return registro, servicios_asociados


# =====================================================================
# 4. GUARDADO Y ACTUALIZACIÓN EN LA BASE DE DATOS
# =====================================================================

def guardar_o_actualizar_db(datos, servicios_seleccionados, catalogo_actual):
    """
    Recibe los datos escritos en el formulario.
    Verifica automáticamente si la orden es NUEVA (hace INSERT)
    o si YA EXISTÍA en la base de datos (hace UPDATE para actualizar los avances).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    fecha_actual = datetime.now() # Toma la fecha y hora exacta del computador
    orden = datos["orden"]

    # Preguntamos a MySQL si ese número de orden ya está registrado
    cursor.execute("SELECT id_orden, id_equipo FROM ORDENES_SERVICIO WHERE id_orden = %s;", (orden,))
    existe = cursor.fetchone()

    if not existe:
        # --- CASO A: LA ORDEN ES NUEVA (SE REGISTRA DESDE CERO) ---
        
        # Paso 1: Guardar el hardware en la tabla EQUIPOS
        cursor.execute(
            "INSERT INTO EQUIPOS (tipo_equipo, marca, modelo, serial) VALUES (%s, %s, %s, %s);",
            (datos["tipo"], datos["marca"], datos["modelo"], datos["serial"])
        )
        id_equipo = cursor.lastrowid # Obtenemos el ID del equipo recién creado

        # Paso 2: Crear la orden de servicio vinculada a ese equipo
        cursor.execute("""
            INSERT INTO ORDENES_SERVICIO (id_orden, id_equipo, fecha_ingreso, estado, falla_cliente, estado_fisico, urgencia)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (orden, id_equipo, fecha_actual, datos["estado_orden"], datos["falla_cli"], datos["est_fisico"], datos["urgencia"]))

        # Paso 3: Crear la ficha técnica con el prediagnóstico, SMART y diagnóstico
        cursor.execute("""
            INSERT INTO FICHAS_TECNICAS (id_orden, salud_smart, prediagnostico_inicial, 
                                        diagnostico_definitivo, solucion_tecnica, observaciones_garantia, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (orden, datos["smart"], datos["prediag"], datos["diag"], datos["solucion"], datos["obs"], fecha_actual))
        id_ficha = cursor.lastrowid
        accion = "registrada"

    else:
        # --- CASO B: LA ORDEN YA EXISTE (SE ACTUALIZA SU PROGRESO EN EL TALLER) ---
        id_equipo = existe[1] # Recuperamos el ID del equipo que ya estaba guardado
        
        # Paso 1: Actualizar datos del equipo por si se corrigió el serial o modelo
        cursor.execute(
            "UPDATE EQUIPOS SET tipo_equipo=%s, marca=%s, modelo=%s, serial=%s WHERE id_equipo=%s;",
            (datos["tipo"], datos["marca"], datos["modelo"], datos["serial"], id_equipo)
        )

        # Paso 2: Actualizar el estado de la orden (ej. pasar de "En mesa" a "Listo para entrega")
        cursor.execute("""
            UPDATE ORDENES_SERVICIO 
            SET estado=%s, falla_cliente=%s, estado_fisico=%s, urgencia=%s 
            WHERE id_orden=%s;
        """, (datos["estado_orden"], datos["falla_cli"], datos["est_fisico"], datos["urgencia"], orden))

        # Paso 3: Actualizar los hallazgos técnicos en la ficha
        cursor.execute("""
            UPDATE FICHAS_TECNICAS 
            SET salud_smart=%s, prediagnostico_inicial=%s, 
                diagnostico_definitivo=%s, solucion_tecnica=%s, observaciones_garantia=%s, fecha_registro=%s
            WHERE id_orden=%s;
        """, (datos["smart"], datos["prediag"], datos["diag"], datos["solucion"], datos["obs"], fecha_actual, orden))

        # Buscamos el ID de la ficha técnica actual
        cursor.execute("SELECT id_ficha FROM FICHAS_TECNICAS WHERE id_orden = %s;", (orden,))
        id_ficha = cursor.fetchone()[0]

        # Borramos temporalmente la lista vieja de servicios de esta orden para guardar la lista actualizada
        cursor.execute("DELETE FROM DETALLE_SERVICIOS_FICHA WHERE id_ficha = %s;", (id_ficha,))
        accion = "actualizada"

    # Paso 4 (Común para ambos casos): Guardar todos los servicios aplicados de la lista
    for serv in servicios_seleccionados:
        id_serv = catalogo_actual[serv]
        cursor.execute("INSERT INTO DETALLE_SERVICIOS_FICHA (id_ficha, id_servicio) VALUES (%s, %s);", (id_ficha, id_serv))

    # Confirmamos todos los pasos anteriores en la base de datos
    conexion.commit()
    cursor.close()
    conexion.close()
    return accion, fecha_actual


# =====================================================================
# 5. GENERACIÓN DE REPORTES (FICHA .TXT Y RESUMEN PARA SISTEMA WEB)
# =====================================================================

def generar_archivo_ficha_csv(datos, servicios_seleccionados, fecha_actual):
    """
    Guarda o anexa la ficha técnica como una sola línea en formato CSV compatible con Excel.
    """
    os.makedirs("reportes_csv", exist_ok=True)
    nombre_archivo = "reportes_csv/fichas_tecnicas.csv"

    def limpiar_texto(valor):
        if not valor:
            return ""
        texto = str(valor).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
        texto = texto.replace('"', '""')
        return f'"{texto}"'

    nro_orden = str(datos.get("orden", "")).strip()
    urgencia = str(datos.get("urgencia", "")).strip()
    fecha_reg = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
    tipo_disp = str(datos.get("tipo", "")).strip()
    marca_modelo = f"{datos.get('marca', '')} {datos.get('modelo', '')}".strip()
    serial_sn = str(datos.get("serial", "")).strip()
    estado_entrada = limpiar_texto(datos.get("est_fisico", ""))
    falla_reportada = limpiar_texto(datos.get("falla_cli", ""))
    smart_status = str(datos.get("smart", "")).strip()
    detalle_prediag = limpiar_texto(datos.get("prediag", ""))
    servicios_str = limpiar_texto("|".join(servicios_seleccionados))
    diag_definitivo = limpiar_texto(datos.get("diag", ""))
    solucion_realizada = limpiar_texto(datos.get("solucion", ""))
    observaciones = limpiar_texto(datos.get("obs", ""))
    estado_final = str(datos.get("estado_orden", "")).strip()

    linea_csv = (
        f"{nro_orden},{urgencia},{fecha_reg},{tipo_disp},{marca_modelo},{serial_sn},"
        f"{estado_entrada},{falla_reportada},{smart_status},{detalle_prediag},"
        f"{servicios_str},{diag_definitivo},{solucion_realizada},{observaciones},{estado_final}\n"
    )

    archivo_nuevo = not os.path.exists(nombre_archivo)
    with open(nombre_archivo, "a", encoding="utf-8-sig") as f:
        if archivo_nuevo:
            cabecera = (
                "Nro_Orden,Urgencia,Fecha_Registro,Tipo_Dispositivo,Marca_Modelo,Serial,"
                "Estado_Entrada,Falla_Reportada,Smart_Status,Detalle_Prediagnostico,"
                "Servicios_Realizados,Diagnostico_Definitivo,Solucion_Realizada,Observaciones,Estado_Final\n"
            )
            f.write(cabecera)
        f.write(linea_csv)

    return nombre_archivo


def construir_resumen_web(datos, servicios_seleccionados):
    """
    Arma un texto compacto y ordenado listo para copiar al portapapeles (Ctrl + C)
    y pegarlo (Ctrl + V) en el software administrativo web que usa recepción.
    """
    servicios_txt = ", ".join(servicios_seleccionados) if servicios_seleccionados else "Pendiente por autorizar"
    return (
        f"--- REPORTE TÉCNICO COMPUMEP (ORDEN: {datos['orden']}) ---\n"
        f"EQUIPO: {datos['tipo']} {datos['marca']} {datos['modelo']}\n"
        f"ESTADO EN TALLER: {datos['estado_orden']}\n"
        f"FALLA REPORTADA: {datos['falla_cli']}\n"
        f"ESTADO SMART: {datos['smart']}\n"
        f"PREDIAGNÓSTICO INICIAL (MESA): {datos['prediag'] or 'N/A'}\n"
        f"DIAGNÓSTICO TÉCNICO: {datos['diag'] or 'En proceso'}\n"
        f"SERVICIOS REALIZADOS: {servicios_txt}\n"
        f"SOLUCIÓN / TRABAJO REALIZADO: {datos['solucion'] or 'En banco'}\n"
        f"OBSERVACIONES / SALVEDADES: {datos['obs'] or 'Sin salvedades de garantía'}\n"
        f"------------------------------------------------"
    )