import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 for å hente fartsgrenser via relasjoner...")
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    # Her ber vi spesifikt om 'relasjoner' - det er her 105 er koblet til 103
    params = {
        'inkluder': 'geometri,egenskaper,relasjoner,metadata',
        'srid': '4326'
    }
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Server-feil: {response.status_code}")
            return

        data = response.json()
        alle_rader = []

        for obj in data.get('objekter', []):
            try:
                # 1. Posisjon
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                if len(coords) < 2: continue
                lon, lat = coords[0], coords[1]

                # 2. Finn fartsgrense via relasjoner (Objekt 105)
                fart = "80" 
                
                # Vi leter i 'relasjoner' -> 'foreldre' (Fartsgrense eier ofte boksen logisk)
                # eller 'barn' avhengig av hvordan NVDB er indeksert i dag
                relasjoner = obj.get('relasjoner', {})
                for rel_type in ['foreldre', 'barn']:
                    for r in relasjoner.get(rel_type, []):
                        if r.get('type', {}).get('id') == 105:
                            # Her fant vi en fartsgrense-kobling! 
                            # Vi henter verdien fra vegobjektet i relasjonen
                            for e in r.get('vegobjekt', {}).get('egenskaper', []):
                                if e.get('id') == 2021:
                                    fart = str(e.get('verdi', '80'))
                                    break
                
                # Hvis vi fortsatt ikke har funnet den, sjekker vi egenskaper direkte
                if fart == "80":
                    for e in obj.get('egenskaper', []):
                        if "fartsgrense" in str(e.get('navn', '')).lower():
                            fart = str(e.get('verdi', '80'))
                            break

                fart = "".join(filter(str.isdigit, fart))
                if not fart: fart = "80"

                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])
            except:
                continue

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"Ferdig! Lagret {len(alle_rader)} punkter.")
        # En liten sjekk i loggen din:
        print(f"Sjekk: Første 5 fartsgrenser i lista: {[r[3] for r in alle_rader[:5]]}")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
