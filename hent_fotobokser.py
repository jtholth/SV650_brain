import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB V4)...")
    
    # Vi henter 103 og 823, og inkluderer vegsegmenter for å få fartsgrense
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    params = {
        'inkluder': 'geometri,vegsegmenter,metadata',
        'srid': '4326',
        'vegsystemreferanse': 'E,R,F'
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
        
        # Vi åpner fila med en gang
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            total = 0

            for obj in data.get('objekter', []):
                try:
                    # Hent koordinater
                    wkt = obj['geometri']['wkt']
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                    if len(coords) < 2: continue
                    lon, lat = coords[0], coords[1]

                    # HENT EKTE FARTSGRENSE FRA VEGSEGMENTET
                    # Dette er data fra objekt 105 som er "limt" på boks-punktet
                    fart = "80" 
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        seg = obj['vegsegmenter'][0]
                        if 'fartsgrense' in seg:
                            fart = str(seg['fartsgrense'])
                    
                    # Rens farten for tekst
                    fart = "".join(filter(str.isdigit, fart))
                    if not fart: fart = "80"

                    type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                    writer.writerow([type_id, lat, lon, fart])
                    total += 1
                except:
                    continue
                    
        print(f"Suksess! Lagret {total} punkter i ATK.csv.")

    except Exception as e:
        print(f"Krasj underveis: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
