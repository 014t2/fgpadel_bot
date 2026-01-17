import requests
from bs4 import BeautifulSoup
import re, os, json, gspread, time
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

def obtener_credenciales(scope):
    creds_raw = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_raw:
        raise ValueError("❌ No se encontró GOOGLE_CREDENTIALS")
    if creds_raw.strip().startswith('{'):
        return ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_raw), scope)
    return ServiceAccountCredentials.from_json_keyfile_name(creds_raw, scope)

def limpiar_y_separar(texto_sucio):
    texto_limpio = texto_sucio.replace('\xa0', ' ').strip()
    partes = texto_limpio.split()
    if not partes: return "", ""
    nombre = partes[0].title()
    apellidos = " ".join(partes[1:]).title()
    return nombre, apellidos

def actualizar_ranking():
    print("📊 Iniciando actualización de ranking (Simulación de Formulario)...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds = obtener_credenciales(scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("flujo_jaime")
        
        session = requests.Session()
        url_ranking = "https://fgpadel.es/Rankings.asp"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://fgpadel.es',
            'Referer': url_ranking,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Valores del selector HTML: 1 para Masculino, 2 para Femenino
        categorias = [("1", "Datos"), ("2", "Datos F")]

        for valor_rnk, nombre_hoja in categorias:
            print(f"🔎 Enviando formulario para: {nombre_hoja}...")
            
            # Datos que enviamos al formulario POST
            payload = {'rnk': valor_rnk}
            
            # Hacemos la petición POST
            response = session.post(url_ranking, headers=headers, data=payload, timeout=20)
            response.encoding = 'iso-8859-1' 
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tabla = soup.find('table', class_='standard-table')

            if not tabla:
                print(f"❌ La web no generó la tabla para {nombre_hoja} tras el envío.")
                continue

            filas = tabla.find_all('tr')
            datos_para_subir = []

            for f in filas:
                cols = f.find_all('td')
                if len(cols) >= 3:
                    pos = cols[0].get_text(strip=True)
                    if not pos.isdigit(): continue

                    enlace_a = cols[1].find('a')
                    nombre_raw = enlace_a.get_text(strip=True) if enlace_a else cols[1].get_text(strip=True)
                    url_perfil = f"https://fgpadel.es/{enlace_a.get('href', '')}" if enlace_a else ""
                    
                    div_puntos = cols[2].find('div', class_='centrado') or cols[2]
                    puntos = div_puntos.get_text(strip=True)

                    nombre, apellidos = limpiar_y_separar(nombre_raw)
                    datos_para_subir.append([nombre, apellidos, pos, puntos, url_perfil])
            
            if datos_para_subir:
                hoja = spreadsheet.worksheet(nombre_hoja)
                hoja.clear()
                hoja.append_row(["nombre", "apellidos", "posicion", "puntos", "perfil"])
                hoja.append_rows(datos_para_subir)
                print(f"✅ Hoja '{nombre_hoja}' actualizada ({len(datos_para_subir)} filas).")
            
            time.sleep(2)

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    actualizar_ranking()