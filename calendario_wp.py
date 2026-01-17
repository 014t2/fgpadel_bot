import requests
import os
import base64
import re
from scraper import obtener_torneos
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv('WP_URL')
WP_USER = os.getenv('WP_USER')
WP_PASSWORD = os.getenv('WP_APP_PASSWORD')

def obtener_cabeceras():
    credenciales = f"{WP_USER}:{WP_PASSWORD}"
    token = base64.b64encode(credenciales.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

def limpiar_texto(texto):
    """Elimina caracteres raros, símbolos como ª o º y espacios extra"""
    # Reemplaza símbolos de orden (ª, º) por letras normales o nada
    texto = texto.replace("ª", "a").replace("º", "o").replace("1.", "1")
    # Elimina cualquier cosa que no sea letra, número, espacio o guion
    texto_limpio = re.sub(r'[^a-zA-Z0-9\sÁÉÍÓÚáéíóúÑñ-]', '', texto)
    # Limpia espacios dobles
    return " ".join(texto_limpio.split())

def traducir_fecha_a_iso(fecha_texto):
    """Convierte '16 Feb-22 Feb' en fechas ISO reales"""
    meses_map = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12
    }
    
    año_actual = datetime.now().year
    matches = re.findall(r'(\d+)\s+([a-zA-Z]{3})', fecha_texto.lower())
    
    if not matches:
        hoy = datetime.now().strftime("%Y-%m-%d")
        return hoy + " 09:00:00", hoy + " 21:00:00"

    # Fecha inicio
    dia_ini, mes_str_ini = matches[0]
    mes_ini = meses_map.get(mes_str_ini, datetime.now().month)
    f_inicio = f"{año_actual}-{mes_ini:02d}-{int(dia_ini):02d} 09:00:00"

    # Fecha fin
    dia_fin, mes_str_fin = matches[-1]
    mes_fin = meses_map.get(mes_str_fin, mes_ini)
    f_fin = f"{año_actual}-{mes_fin:02d}-{int(dia_fin):02d} 21:00:00"

    return f_inicio, f_fin

def publicar_en_calendario(torneo):
    if torneo['finalizado']:
        return

    # APLICAMOS LIMPIEZA AL TÍTULO
    titulo_limpio = limpiar_texto(torneo['nombre'])
    f_inicio, f_fin = traducir_fecha_a_iso(torneo['fecha'])
    
    endpoint = f"{WP_URL}/wp-json/tribe/events/v1/events"

    payload = {
        "title": titulo_limpio,
        "description": f"Torneo oficial de pádel. Fecha original: {torneo['fecha']}",
        "start_date": f_inicio,
        "end_date": f_fin,
        "status": "publish"
    }

    # Verificar duplicados con el título limpio
    check = requests.get(f"{endpoint}?search={titulo_limpio}", headers=obtener_cabeceras())
    if check.status_code == 200 and len(check.json().get('events', [])) > 0:
        print(f"⏭️ Saltando (ya existe): {titulo_limpio}")
        return

    res = requests.post(endpoint, json=payload, headers=obtener_cabeceras())
    if res.status_code == 201:
        print(f"🗓️ Evento creado: {titulo_limpio} ({f_inicio})")
    else:
        print(f"❌ Error {res.status_code} en: {titulo_limpio}")

if __name__ == "__main__":
    print("🚀 Iniciando sincronización limpia...")
    lista = obtener_torneos()
    for t in lista:
        publicar_en_calendario(t)