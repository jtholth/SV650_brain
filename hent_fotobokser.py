import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 og henter fartsgrenser via vegsystem...")
    
    # Vi henter både punkt (103) og strekning (823)
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    params = {
        'inkluder': 'geometri,vegsegmenter,metadata',
        'srid': '4326',
        'vegsystemreferanse': 'E,R,F' # Europavei, Riksvei, Fylkesvei
    }
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Feil: {response.status_code}")
            return

        data = response.json()
        
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            antall = 0

            for obj in data.get('objekter', []):
                try:
                    # 1. Hent koordinater
                    wkt = obj['geometri']['wkt']
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                    if len(coords) < 2: continue
                    lon, lat = coords[0], coords[1]

                    # 2. Finn fartsgrense i vegsegmentet
                    # Det er her vegsystemreferansen kobles til fartsgrense (105)
                    fart = "80" 
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        # Vi ser på det første segmentet boksen er tilknyttet
                        segment = obj['vegsegmenter'][0]
                        if 'fartsgrense' in segment:
                            fart = str(segment['fartsgrense'])
                        elif 'detaljert_vegsystemreferanse' in segment:
                            # Noen ganger ligger det dypere i metadataene
                            fart = str(segment.get('fartsgrense', '80'))

                    # Rens farten (kun tall)
                    fart = "".join(filter(str.isdigit, fart))
                    if not fart or fart == "0": fart = "80"

                    type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                    
                    writer.writerow([type_id, lat, lon, fart])
                    antall += 1
                except:
                    continue

        print(f"Suksess! Lagret {antall} punkter. Sjekk fila nå!")

    except Exception as e:
        print(f"Feil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
