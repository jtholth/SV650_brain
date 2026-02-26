import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 for å hente bokser med tilhørende fartsgrense (105)...")
    
    # URL for å hente fotobokser
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    # Her er trikset: 'inkluder=fellesstrekning' henter objekter som overlapper
    params = {
        'inkluder': 'geometri,egenskaper,fellesstrekning',
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
            print(f"Feil: {response.status_code}")
            return

        data = response.json()
        
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            antall = 0

            for obj in data.get('objekter', []):
                # 1. Finn posisjon
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                if len(coords) < 2: continue
                lon, lat = coords[0], coords[1]

                # 2. Finn fartsgrense (Objekt 105) via fellesstrekning
                fart = "80" # Default
                
                # Vi leter gjennom fellesstrekninger for å finne objekt 105
                for strekning in obj.get('fellesstrekninger', []):
                    for vegobjekt in strekning.get('vegobjekter', []):
                        if vegobjekt.get('type') == 105:
                            # Inne i objekt 105 leter vi etter egenskap 2021 (Fartsgrense)
                            for egenskap in vegobjekt.get('egenskaper', []):
                                if egenskap.get('id') == 2021:
                                    fart = str(egenskap.get('verdi', '80'))
                                    break
                
                # Vask farten for tekst
                fart = "".join(filter(str.isdigit, fart))
                
                # Type: 1 for 103 (Punkt), 2 for 823 (Strekning)
                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                
                writer.writerow([type_id, lat, lon, fart])
                antall += 1

        print(f"Suksess! Lagret {antall} punkter med ekte fartsgrenser fra objekt 105.")

    except Exception as e:
        print(f"En feil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
