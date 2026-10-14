##Irvin Misael Mejia Hernandez GTIR246
## Actividad R1


import os
from datetime import datetime

# Nombres de archivos (rutas relativas: misma carpeta del programa)
ARCHIVOS_ENTRADA = ["router_metrics.csv", "router_metrics.txt"]
ARCHIVO_REPORTE = "reporte_qos.txt"

# Límites del SLA (se alerta solo si se SUPERAN, no si son iguales)
LIMITE_LATENCIA_MS = 150
LIMITE_PERDIDA_PORCENTAJE = 5

ESTADOS_VALIDOS = ["UP", "DEGRADED", "DOWN"]


def encontrar_archivo_entrada():
    # Busca el archivo de métricas en la carpeta actual
    for nombre in ARCHIVOS_ENTRADA:
        if os.path.exists(nombre):
            return nombre
    return None


def procesar_linea(linea):
    # Valida una línea y devuelve sus datos convertidos, o None si es inválida
    campos = linea.strip().split(",")
    if len(campos) != 7:
        return None

    id_router = campos[1].strip()
    estado = campos[6].strip().upper()

    if id_router == "" or estado not in ESTADOS_VALIDOS:
        return None

    try:
        latencia = float(campos[3])
        enviados = int(campos[4])
        perdidos = int(campos[5])
    except ValueError:
        return None

    if latencia < 0 or enviados <= 0 or perdidos < 0 or perdidos > enviados:
        return None

    return id_router, latencia, enviados, perdidos, estado


def leer_archivo(nombre_archivo):
    # Lee el archivo línea por línea y acumula los datos por router
    datos_routers = {}
    registros_validos = 0
    registros_omitidos = 0
    primera_linea = True

    with open(nombre_archivo, "r", encoding="utf-8-sig", errors="replace") as archivo:
        for linea in archivo:
            if linea.strip() == "":
                continue

            # Si la primera línea es el encabezado, no se cuenta como registro
            if primera_linea:
                primera_linea = False
                if linea.strip().lower().startswith("timestamp"):
                    continue

            registro = procesar_linea(linea)
            if registro is None:
                registros_omitidos += 1
                continue

            id_router, latencia, enviados, perdidos, estado = registro

            if id_router not in datos_routers:
                datos_routers[id_router] = {
                    "suma_latencia": 0.0,
                    "muestras": 0,
                    "enviados": 0,
                    "perdidos": 0,
                    "muestras_down": 0,
                }

            acumulado = datos_routers[id_router]
            acumulado["suma_latencia"] += latencia
            acumulado["muestras"] += 1
            acumulado["enviados"] += enviados
            acumulado["perdidos"] += perdidos
            if estado == "DOWN":
                acumulado["muestras_down"] += 1

            registros_validos += 1

    return datos_routers, registros_validos, registros_omitidos


def calcular_metricas(datos_routers):
    # Calcula las métricas finales de cada router
    metricas = {}
    for id_router in datos_routers:
        acumulado = datos_routers[id_router]

        if acumulado["muestras"] > 0:
            latencia_promedio = acumulado["suma_latencia"] / acumulado["muestras"]
            porcentaje_down = acumulado["muestras_down"] / acumulado["muestras"] * 100
        else:
            latencia_promedio = 0.0
            porcentaje_down = 0.0

        if acumulado["enviados"] > 0:
            porcentaje_perdida = acumulado["perdidos"] / acumulado["enviados"] * 100
        else:
            porcentaje_perdida = 0.0

        metricas[id_router] = {
            "latencia_promedio": latencia_promedio,
            "porcentaje_perdida": porcentaje_perdida,
            "porcentaje_down": porcentaje_down,
        }
    return metricas


def detectar_violaciones_sla(metricas):
    # Devuelve la lista de routers que superan algún límite del SLA
    alertas = []
    for id_router in sorted(metricas):
        latencia = metricas[id_router]["latencia_promedio"]
        perdida = metricas[id_router]["porcentaje_perdida"]
        motivos = []

        if latencia > LIMITE_LATENCIA_MS:
            motivos.append(f"Latencia promedio > {LIMITE_LATENCIA_MS} ms")
        if perdida > LIMITE_PERDIDA_PORCENTAJE:
            motivos.append(f"Pérdida de paquetes > {LIMITE_PERDIDA_PORCENTAJE}%")

        if len(motivos) > 0:
            alertas.append((id_router, latencia, perdida, " y ".join(motivos)))
    return alertas


def generar_reporte(metricas, alertas, registros_validos, registros_omitidos, nombre_entrada):
    # Escribe el reporte final en reporte_qos.txt
    separador = "=" * 70
    subseparador = "-" * 70
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ARCHIVO_REPORTE, "w", encoding="utf-8") as reporte:
        reporte.write(separador + "\n")
        reporte.write("REPORTE DE MONITOREO DE CALIDAD DE SERVICIO (QoS)\n")
        reporte.write(separador + "\n")
        reporte.write(f"Fecha de procesamiento : {fecha}\n")
        reporte.write(f"Archivo analizado      : {nombre_entrada}\n")
        reporte.write(f"Registros procesados   : {registros_validos}\n")
        reporte.write(f"Registros omitidos     : {registros_omitidos}\n\n")

        if len(metricas) == 0:
            reporte.write("No se encontraron registros válidos para analizar.\n")
            return

        reporte.write("1. LATENCIA PROMEDIO Y PÉRDIDA DE PAQUETES POR ROUTER\n")
        reporte.write(subseparador + "\n")
        reporte.write(f"{'Router':<20}{'Latencia prom. (ms)':>22}{'Pérdida (%)':>16}\n")
        reporte.write(subseparador + "\n")
        for id_router in sorted(metricas):
            latencia = metricas[id_router]["latencia_promedio"]
            perdida = metricas[id_router]["porcentaje_perdida"]
            reporte.write(f"{id_router:<20}{latencia:>22.2f}{perdida:>16.2f}\n")

        reporte.write("\n2. ALERTAS DE VIOLACIÓN DE SLA\n")
        reporte.write(subseparador + "\n")
        reporte.write(f"Límites: latencia promedio > {LIMITE_LATENCIA_MS} ms "
                      f"o pérdida de paquetes > {LIMITE_PERDIDA_PORCENTAJE}%\n")
        if len(alertas) == 0:
            reporte.write("Ningún router incumple el SLA.\n")
        else:
            for id_router, latencia, perdida, motivo in alertas:
                reporte.write(f"[ALERTA] Router {id_router}\n")
                reporte.write(f"   Latencia promedio : {latencia:.2f} ms\n")
                reporte.write(f"   Pérdida de paquetes: {perdida:.2f} %\n")
                reporte.write(f"   Motivo            : {motivo}\n")

        reporte.write("\n3. DISPONIBILIDAD (% DE MUESTRAS EN ESTADO DOWN)\n")
        reporte.write(subseparador + "\n")
        reporte.write(f"{'Router':<20}{'Muestras en DOWN (%)':>24}\n")
        reporte.write(subseparador + "\n")
        for id_router in sorted(metricas):
            reporte.write(f"{id_router:<20}{metricas[id_router]['porcentaje_down']:>24.2f}\n")

        reporte.write("\nNota: el porcentaje DOWN se calcula sobre el número de muestras,\n")
        reporte.write("ya que el intervalo entre mediciones no está definido en los datos.\n")
        reporte.write(separador + "\n")


def main():
    nombre_entrada = encontrar_archivo_entrada()
    if nombre_entrada is None:
        print("Error: no se encontró router_metrics.csv ni router_metrics.txt "
              "en la carpeta del programa.")
        return

    try:
        datos_routers, validos, omitidos = leer_archivo(nombre_entrada)
    except OSError as error:
        print(f"Error al abrir o leer el archivo: {error}")
        return

    metricas = calcular_metricas(datos_routers)
    alertas = detectar_violaciones_sla(metricas)

    try:
        generar_reporte(metricas, alertas, validos, omitidos, nombre_entrada)
    except OSError as error:
        print(f"Error al crear el reporte: {error}")
        return

    print(f"Análisis completado. Registros válidos: {validos}, omitidos: {omitidos}.")
    print(f"Reporte generado: {ARCHIVO_REPORTE}")


main()
