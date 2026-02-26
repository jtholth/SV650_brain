import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4...")
    # Vi henter fotobokser (103) og strekningsmåling (823)
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    # Her ber vi om vegsegmenter - det er der vegsystemreferanse og fartsgrense ligger i V4
    params = {
        'inkluder': 'geometri,vegsegmenter,metadata',
        'srid': '4326'
    }
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Feil fra server: {response.status_code}")
            return

        data = response.json()
        
        # Vi åpner fila med en gang for å sikre at den eksisterer for Git
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            total = 0

            for obj in data.get('objekter', []):
                try:
                    # 1. Koordinater
                    wkt = obj['geometri']['wkt']
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                    if len(coords) < 2: continue
                    lon, lat = coords[0], coords[1]

                    # 2. Fartsgrense fra vegsystemreferanse i vegsegmentet
                    fart = "80" 
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        # V4 lagrer fartsgrensen direkte på vegsegmentet
                        segment = obj['vegsegmenter'][0]
                        fart = str(segment.get('fartsgrense', '80'))
                    
                    # Rens farten (kun tall)
                    fart = "".join(filter(str.isdigit, fart))
                    if not fart or fart == "0": fart = "80"

                    type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                    writer.writerow([type_id, lat, lon, fart])
                    total += 1
                except:
                    continue
                    
        print(f"Suksess! Lagret {total} punkter i ATK.csv.")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
