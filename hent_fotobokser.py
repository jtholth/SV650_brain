import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til NVDB V4... Bruker din logikk for stedfesting.")
    
    objekttyper = ["103", "823"]
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_data = []

    for o_type in objekttyper:
        print(f"Henter type {o_type}...")
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
        
        # Vi inkluderer 'vegsegmenter' - det er HER m485 og fartsgrensen kobles!
        params = {
            'inkluder': 'geometri,vegsegmenter,metadata',
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

                    # 2. Hent fartsgrensen fra vegsegmentet (veien den står på)
                    fart = "80" 
                    if 'vegsegmenter' in obj:
                        for seg in obj['vegsegmenter']:
                            # Sjekker om segmentet (veibiten) har fartsgrense registrert
                            v = seg.get('fartsgrense')
                            if v:
                                fart = str(v)
                                break
                    
                    type_id = 1 if o_type == "103" else 2
                    alle_data.append([type_id, lat, lon, fart])
            else:
                print(f"Feil {response.status_code} på {o_type}")
        except Exception as e:
            print(f"Feil: {e}")

    # Skriv til fil
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_data)
        
    print(f"FERDIG! Lagret {len(alle_data)} rader.")
    if alle_data:
        # Finn noen eksempler som IKKE er 80 for å bevise at det funker
        unike_farter = set([r[3] for r in alle_data])
        print(f"Fant følgende fartsgrenser i dataene: {unike_farter}")

if __name__ == "__main__":
    hent_norske_fotobokser()
