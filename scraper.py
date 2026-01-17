import requests
from bs4 import BeautifulSoup
from datetime import datetime

def obtener_torneos():
    url = "https://fgpadel.es/calendario.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    meses_nombres = {
        1: ["enero", "urtarrilak", "ene"],
        2: ["febrero", "otsailak", "feb"],
        3: ["marzo", "martxoak", "mar"],
        4: ["abril", "apirilak", "abr"],
        5: ["mayo", "maiatzak", "may"],
        6: ["junio", "ekainak", "jun"],
        7: ["julio", "uztailak", "jul"],
        8: ["agosto", "abuztuak", "ago"],
        9: ["septiembre", "irailak", "sep"],
        10: ["octubre", "urriak", "oct"],
        11: ["noviembre", "azaroak", "nov"],
        12: ["diciembre", "abenduak", "dic"]
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        torneos = []
        filas = soup.find_all('tr')
        
        ahora = datetime.now()
        dia_actual = ahora.day
        mes_actual = ahora.month
        palabras_mes_actual = meses_nombres[mes_actual]

        for fila in filas:
            cols = fila.find_all('td')
            # Según tu imagen: cols[1] es Fecha, cols[2] es Nombre
            if len(cols) >= 3:
                fecha_texto = cols[1].get_text(strip=True).lower()
                nombre = cols[2].get_text(strip=True)

                if any(char.isdigit() for char in fecha_texto) and len(nombre) > 5:
                    finalizado = False
                    
                    # 1. Detección por palabras clave (Si la web ya dice explícitamente que terminó)
                    texto_completo = fila.get_text().lower()
                    if any(p in texto_completo for p in ["finalizado", "cuadros", "acta", "resultados"]):
                        finalizado = True
                    
                    # 2. Lógica de fecha solicitada
                    try:
                        numeros = [int(s) for s in fecha_texto.replace('-', ' ').split() if s.isdigit()]
                        if numeros:
                            dia_fin_torneo = numeros[-1]
                            es_mes_actual = any(p in fecha_texto for p in palabras_mes_actual)
                            
                            # ARCHIVAR SOLO SI: Es el mes actual Y el día actual es MAYOR al día de fin
                            if es_mes_actual and dia_actual > dia_fin_torneo:
                                finalizado = True
                            
                            # Si el mes es anterior al actual, también se archiva
                            meses_futuros_o_actual = []
                            for m in range(mes_actual, 13):
                                meses_futuros_o_actual.extend(meses_nombres[m])
                            
                            if not any(p in fecha_texto for p in meses_futuros_o_actual):
                                finalizado = True
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