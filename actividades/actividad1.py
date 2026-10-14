##Irvin Misael Mejia Hernandez GTIR246
## Actividad R1

import os
import sys
from datetime import datetime

# --- Parámetros configurables ---
ARCHIVO_LOG = "network_traffic.log"
ARCHIVO_REPORTE = "reporte_diagnostico.txt"
FORMATO_FECHA = "%Y-%m-%dT%H:%M:%S"
PUERTOS_VIGILADOS = (22, 3389)
UMBRAL_INTENTOS = 5      # intentos DENY mínimos para generar alerta
VENTANA_SEGUNDOS = 60    # intervalo de tiempo considerado "corto"
CANTIDAD_TOP = 5
PROTOCOLOS_CONOCIDOS = ("TCP", "UDP", "ICMP")


def ip_valida(ip):
    partes = ip.split(".")
    if len(partes) != 4:
        return False
    for parte in partes:
        if not parte.isdigit() or int(parte) > 255:
            return False
    return True


def parsear_linea(linea):
    # Se cambian las comas por espacios para aceptar ambos delimitadores
    campos = linea.replace(",", " ").split()
    if len(campos) != 7:
        return None

    texto_fecha, ip_origen, ip_destino, texto_puerto, protocolo, accion, texto_bytes = campos

    try:
        marca_tiempo = datetime.strptime(texto_fecha, FORMATO_FECHA)
        puerto = int(texto_puerto)
        bytes_transferidos = int(texto_bytes)
    except ValueError:
        return None

    if puerto < 0 or puerto > 65535 or bytes_transferidos < 0:
        return None
    if not ip_valida(ip_origen) or not ip_valida(ip_destino):
        return None

    protocolo = protocolo.upper()
    accion = accion.upper()
    if accion != "ALLOW" and accion != "DENY":
        return None

    return marca_tiempo, ip_origen, ip_destino, puerto, protocolo, accion, bytes_transferidos


def registrar_intento_denegado(intentos_por_clave, alertas, ip_origen, puerto, marca_tiempo):
    # Cada (IP, puerto) guarda solo las marcas de tiempo que siguen dentro de la ventana
    clave = (ip_origen, puerto)
    if clave not in intentos_por_clave:
        intentos_por_clave[clave] = []
    marcas = intentos_por_clave[clave]
    marcas.append(marca_tiempo)

    while (marca_tiempo - marcas[0]).total_seconds() > VENTANA_SEGUNDOS:
        marcas.pop(0)

    # Una sola alerta por (IP, puerto); se conserva el máximo de intentos visto en una ventana
    if len(marcas) >= UMBRAL_INTENTOS:
        if clave not in alertas or len(marcas) > alertas[clave]:
            alertas[clave] = len(marcas)


def procesar_archivo(ruta_log):
    bytes_permitidos_por_ip = {}
    conteo_protocolos = {"TCP": 0, "UDP": 0, "ICMP": 0, "OTROS": 0}
    intentos_por_clave = {}
    alertas = {}
    registros_validos = 0
    lineas_omitidas = 0

    with open(ruta_log, "r", encoding="utf-8", errors="replace") as archivo:
        for linea in archivo:
            if linea.strip() == "":
                continue

            registro = parsear_linea(linea)
            if registro is None:
                lineas_omitidas += 1
                continue

            marca_tiempo, ip_origen, ip_destino, puerto, protocolo, accion, bytes_transferidos = registro
            registros_validos += 1

            if protocolo in PROTOCOLOS_CONOCIDOS:
                conteo_protocolos[protocolo] += 1
            else:
                conteo_protocolos["OTROS"] += 1

            if accion == "ALLOW":
                if ip_origen in bytes_permitidos_por_ip:
                    bytes_permitidos_por_ip[ip_origen] += bytes_transferidos
                else:
                    bytes_permitidos_por_ip[ip_origen] = bytes_transferidos
            elif puerto in PUERTOS_VIGILADOS:
                registrar_intento_denegado(intentos_por_clave, alertas, ip_origen, puerto, marca_tiempo)

    return bytes_permitidos_por_ip, conteo_protocolos, alertas, registros_validos, lineas_omitidas


def formatear_bytes(cantidad):
    if cantidad >= 1024 ** 3:
        return f"{cantidad / 1024 ** 3:.2f} GB"
    if cantidad >= 1024 ** 2:
        return f"{cantidad / 1024 ** 2:.2f} MB"
    if cantidad >= 1024:
        return f"{cantidad / 1024:.2f} KB"
    return f"{cantidad} B"


def obtener_bytes(par_ip_bytes):
    return par_ip_bytes[1]


def obtener_intentos(par_alerta):
    return par_alerta[1]


def calcular_top_talkers(bytes_permitidos_por_ip):
    ordenados = sorted(bytes_permitidos_por_ip.items(), key=obtener_bytes, reverse=True)
    return ordenados[:CANTIDAD_TOP]


def nombre_servicio(puerto):
    if puerto == 22:
        return "SSH"
    if puerto == 3389:
        return "RDP"
    return str(puerto)


def generar_reporte(ruta_reporte, top_talkers, alertas, conteo_protocolos, registros_validos, lineas_omitidas):
    separador = "=" * 70
    fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ruta_reporte, "w", encoding="utf-8") as reporte:
        reporte.write(separador + "\n")
        reporte.write("REPORTE DE DIAGNÓSTICO DE RED\n")
        reporte.write(separador + "\n")
        reporte.write(f"Fecha de procesamiento: {fecha_proceso}\n")
        reporte.write(f"Total de registros procesados correctamente: {registros_validos:,}\n")
        reporte.write(f"Líneas omitidas por errores: {lineas_omitidas:,}\n\n")

        reporte.write(f"TOP {CANTIDAD_TOP} IP ORIGEN POR VOLUMEN DE TRÁFICO PERMITIDO (ALLOW)\n")
        reporte.write("-" * 70 + "\n")
        if len(top_talkers) == 0:
            reporte.write("No se encontraron registros con acción ALLOW.\n")
        else:
            posicion = 1
            for ip, total_bytes in top_talkers:
                reporte.write(f"{posicion}. IP: {ip} | Tráfico: {formatear_bytes(total_bytes)} ({total_bytes:,} bytes)\n")
                posicion += 1
        reporte.write("\n")

        reporte.write("--- ALERTAS DE SEGURIDAD DETECTADAS ---\n")
        reporte.write(f"(Criterio: {UMBRAL_INTENTOS} o más intentos DENY en {VENTANA_SEGUNDOS} segundos)\n")
        if len(alertas) == 0:
            reporte.write("No se detectaron posibles ataques de fuerza bruta o escaneo.\n")
        else:
            for (ip, puerto), intentos in sorted(alertas.items(), key=obtener_intentos, reverse=True):
                servicio = nombre_servicio(puerto)
                reporte.write(
                    f"[ALERTA] Posible ataque {servicio} por fuerza bruta/escaneo desde la IP: {ip} "
                    f"| Puerto: {puerto} | Intentos en ventana: {intentos:,}\n"
                )
        reporte.write("\n")

        reporte.write("--- RESUMEN POR PROTOCOLO ---\n")
        reporte.write(f"(Porcentaje sobre {registros_validos:,} registros válidos)\n")
        if registros_validos == 0:
            reporte.write("No hay registros válidos para calcular porcentajes.\n")
        else:
            for protocolo in ("TCP", "UDP", "ICMP", "OTROS"):
                cantidad = conteo_protocolos[protocolo]
                porcentaje = cantidad * 100 / registros_validos
                reporte.write(f"- {protocolo}: {porcentaje:.2f}% ({cantidad:,} registros)\n")
        reporte.write(separador + "\n")


def main():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    ruta_log = os.path.join(carpeta, ARCHIVO_LOG)
    ruta_reporte = os.path.join(carpeta, ARCHIVO_REPORTE)

    try:
        resultados = procesar_archivo(ruta_log)
    except FileNotFoundError:
        print(f"No se encontró '{ARCHIVO_LOG}' en la carpeta: {carpeta}")
        sys.exit(1)

    bytes_permitidos_por_ip, conteo_protocolos, alertas, registros_validos, lineas_omitidas = resultados
    top_talkers = calcular_top_talkers(bytes_permitidos_por_ip)
    generar_reporte(ruta_reporte, top_talkers, alertas, conteo_protocolos, registros_validos, lineas_omitidas)
    print(f"Reporte generado: {ruta_reporte}")


main()
