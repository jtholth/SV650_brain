import requests
import csv
import re
import time

def hent_norske_fotobokser():
    print("Henter fotobokser og sjekker fartsgrense via koordinat-oppslag...")
    
    # Steg 1: Hent alle fotobokser (103 og 823)
    # Vi bruker 'vegsegmenter' for å få koordinater og vegreferanse i ett
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Kunne ikke hente bokser. Status: {response.status_code}")
            return

        objekter = response.json().get('objekter', [])
        alle_rader = []
        
        print(f"Fant {len(objekter)} bokser. Starter farts-sjekk...")

        for i, obj in enumerate(objekter):
            try:
                # 1. Hent koordinater
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                lon, lat = coords[0], coords[1]

                # 2. FINN FART VED POSISJON (Din meter-logikk, men med GPS)
                # Vi spør etter objekt 105 som overlapper dette punktet
                fart = "80"
                fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                fart_params = {
                    'posisjon': f"{lon},{lat}",
                    'srid': '4326',
                    'inkluder': 'egenskaper'
                }
                
                f_res = requests.get(fart_url, params=fart_params, headers=headers)
                if f_res.status_code == 200:
                    f_data = f_res.json()
                    # Vi tar første treff (det objektet som ligger på veien)
                    if f_data.get('objekter'):
                        egenskaper = f_data['objekter'][0].get('egenskaper', [])
                        for e in egenskaper:
                            if e.get('id') == 2021: # Fartsgrense-ID
                                fart = str(e.get('verdi', '80'))
                                break

                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])

                if (i + 1) % 20 == 0:
                    print(f"Behandlet {i + 1} av {len(objekter)}...")
                    
            except:
                continue

        # Lagre til fila som Git venter på
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        unike = set([r[3] for r in alle_rader])
        print(f"FERDIG! Fant fartsgrenser: {unike}")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
