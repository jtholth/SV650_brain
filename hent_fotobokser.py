import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 (Separat henting for å unngå 404)...")
    
    # Vi henter 103 og 823 hver for seg
    objekttyper = ["103", "823"]
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_data = []

    for o_type in objekttyper:
        print(f"Henter objekttype {o_type}...")
        # I V4 må URL-en være nøyaktig slik:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
        
        params = {
            'inkluder': 'geometri,vegsegmenter',
            'srid': '4326'
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for obj in data.get('objekter', []):
                    # 1. Koordinater
                    wkt = obj['geometri']['wkt']
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                    if len(coords) < 2: continue
                    lon, lat = coords[0], coords[1]

                    # 2. HENT FARTSGRENSE FRA VEGSEGMENTET (Stedfestingen din)
                    fart = "80" 
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        # Vi tar fartsgrensen fra det første segmentet objektet er stedfestet på
                        seg_fart = obj['vegsegmenter'][0].get('fartsgrense')
                        if seg_fart:
                            fart = str(seg_fart)

                    type_id = 1 if o_type == "103" else 2
                    alle_data.append([type_id, lat, lon, fart])
            else:
                print(f"Kunne ikke hente {o_type}. Status: {response.status_code}")
        except Exception as e:
            print(f"Feil ved {o_type}: {e}")

    # Skriv alt til fil
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_data)
        
    print(f"FERDIG! Lagret {len(alle_data)} rader i ATK.csv.")
    if alle_data:
        stikkprove = [r[3] for r in alle_data[:10]]
        print(f"Stikkprøve fartsgrenser: {stikkprove}")

if __name__ == "__main__":
    hent_norske_fotobokser()
