import requests
from bs4 import BeautifulSoup
import re, os, json, gspread
from oauth2client.service_account import ServiceAccountCredentials

def actualizar_ranking():
    print("📊 Iniciando actualización de ranking...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Nombre de tu archivo en Google Sheets
    sheet = client.open("Ranking FGPadel").sheet1 
    sheet.clear()
    sheet.append_row(["Pos", "Nombre", "Apellidos", "Puntos", "Categoría"])

    for id_c, cat in [("1", "Masculino"), ("2", "Femenino")]:
        res = requests.get(f"https://fgpadel.es/Rankings.asp?IdC={id_c}")
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        filas = soup.find_all('tr')[1:]
        
        datos_cat = []
        for f in filas:
            cols = f.find_all('td')
            if len(cols) >= 3:
                raw = re.sub(r'\d+', '', cols[1].get_text(strip=True)).strip()
                partes = raw.split()
                nom = partes[0].title() if partes else ""
                ape = " ".join(partes[1:]).title() if len(partes) > 1 else ""
                puntos = cols[2].get_text(strip=True)
                pos = cols[0].get_text(strip=True)
                datos_cat.append([pos, nom, ape, puntos, cat])
        
        sheet.append_rows(datos_cat)
        print(f"✅ Categoría {cat} actualizada.")

if __name__ == "__main__":
    actualizar_ranking()