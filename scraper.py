import requests
from bs4 import BeautifulSoup
from datetime import datetime

def obtener_torneos():
    url = "https://fgpadel.es/torneos.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Diccionario de meses para que el bot sepa en qué mes estamos (Castellano y Euskera)
    meses_nombres = {
        1: ["enero", "urtarrilak"],
        2: ["febrero", "otsailak"],
        3: ["marzo", "martxoak"],
        4: ["abril", "apirilak"],
        5: ["mayo", "maiatzak"],
        6: ["junio", "ekainak"],
        7: ["julio", "uztailak"],
        8: ["agosto", "abuztuak"],
        9: ["septiembre", "irailak"],
        10: ["octubre", "urriak"],
        11: ["noviembre", "azaroak"],
        12: ["diciembre", "abenduar"]
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        torneos = []
        filas = soup.find_all('tr')
        
        # Datos de tiempo real
        ahora = datetime.now()
        dia_actual = ahora.day
        mes_actual = ahora.month
        palabras_mes_actual = meses_nombres[mes_actual]

        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 2:
                fecha_texto = cols[0].get_text(strip=True).lower()
                nombre = cols[1].get_text(strip=True)

                if any(char.isdigit() for char in fecha_texto) and len(nombre) > 5:
                    finalizado = False
                    
                    # 1. Detección por palabras clave en la fila
                    texto_completo = fila.get_text().lower()
                    if any(palabra in texto_completo for palabra in ["finalizado", "cuadros", "acta", "resultados"]):
                        finalizado = True
                    
                    # 2. Detección automática por fecha
                    try:
                        numeros = [int(s) for s in fecha_texto.replace('-', ' ').split() if s.isdigit()]
                        if numeros:
                            dia_torneo = numeros[0]
                            # Comprobamos si el texto de la fecha contiene el mes actual
                            es_mes_actual = any(p in fecha_texto for p in palabras_mes_actual)
                            
                            # Si es el mes actual y el día ya pasó, marcar como finalizado
                            if es_mes_actual and dia_torneo < dia_actual:
                                finalizado = True
                            # Si la fecha no menciona el mes actual ni meses futuros, 
                            # asumimos que es un mes pasado
                            # (Opcional: podrías refinar esto más, pero para el uso diario basta)
                    except:
                        pass

                    torneos.append({
                        'nombre': nombre,
                        'fecha': fecha_texto.capitalize(),
                        'finalizado': finalizado
                    })
        
        return torneos
    except Exception as e:
        print(f"❌ Error en scraper: {e}")
        return []

if __name__ == "__main__":
    datos = obtener_torneos()
    for t in datos:
        status = "🔴 [ARCHIVAR]" if t['finalizado'] else "🟢 [ACTIVO]"
        print(f"{status} {t['nombre']} - {t['fecha']}")