import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4...")
    # Vi henter 103 og 823 hver for seg for å minske belastningen på serveren
    typer = ["103", "823"]
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_rader = []

    for t in typer:
        print(f"Henter type {t}...")
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{t}"
        params = {
            'inkluder': 'geometri,vegsegmenter',
            'srid': '4326'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for obj in data.get('objekter', []):
                    try:
                        # Posisjon
                        wkt = obj['geometri']['wkt']
                        coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                        if len(coords) < 2: continue
                        lon, lat = coords[0], coords[1]

                        # Fartsgrense fra vegsegment
                        fart = "80"
                        if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                            # Hent fartsgrense direkte fra segment-data
                            fart = str(obj['vegsegmenter'][0].get('fartsgrense', '80'))
                        
                        fart = "".join(filter(str.isdigit, fart))
                        if not fart: fart = "80"

                        type_id = 1 if t == "103" else 2
                        alle_rader.append([type_id, lat, lon, fart])
                    except:
                        continue
            else:
                print(f"Server svarte med {response.status_code} for type {t}")
        except Exception as e:
            print(f"Feil ved henting av type {t}: {e}")

    # VIKTIG: Skriv fila til slutt, uansett om vi fant data eller ikke
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
        
    print(f"Ferdig! Lagret {len(alle_rader)} rader i ATK.csv.")

if __name__ == "__main__":
    hent_norske_fotobokser()
