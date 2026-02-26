import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 med fokus på stedfesting...")
    
    # Vi henter 103 (Fast ATK) og 823 (Strekning)
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    # Vi inkluderer vegsegmenter - det er her fartsgrensen fra stedfestingen ligger
    params = {
        'inkluder': 'geometri,vegsegmenter,egenskaper',
        'srid': '4326'
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
        alle_rader = []

        for obj in data.get('objekter', []):
            try:
                # 1. Hent posisjon (GPS)
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                if len(coords) < 2: continue
                lon, lat = coords[0], coords[1]

                # 2. Hent fartsgrense fra STEDFESTINGEN (vegsegmenter)
                fart = "80" # Default
                
                # Vi sjekker vegsegmenter først, da dette er mest nøyaktig for stedfesting
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    for segment in obj['vegsegmenter']:
                        # Sjekker om segmentet har en direkte fartsgrense-verdi
                        v = segment.get('fartsgrense')
                        if v:
                            fart = str(v)
                            break
                
                # Hvis ikke funnet i segment, sjekk egenskaper som backup
                if fart == "80":
                    for e in obj.get('egenskaper', []):
                        if e.get('id') == 2021 or "fart" in str(e.get('navn', '')).lower():
                            fart = str(e.get('verdi', '80'))
                            break

                # Rens farten for tekst (f.eks "70 km/t" -> "70")
                fart = "".join(filter(str.isdigit, fart))
                if not fart or fart == "0": fart = "80"

                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])
            except:
                continue

        # Lagre til fil
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"Ferdig! Lagret {len(alle_rader)} punkter.")
        
        # Sjekk de første resultatene i loggen
        test_fart = [r[3] for r in alle_rader[:10]]
        print(f"Stikkprøve fartsgrenser: {test_fart}")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
