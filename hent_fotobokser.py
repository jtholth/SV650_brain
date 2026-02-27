import requests
import csv
import re

def hent_norske_fotobokser():
    print("Henter fotobokser med relasjons-sjekk...")
    
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    params = {
        'inkluder': 'geometri,relasjoner,metadata',
        'srid': '4326'
    }
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"Feil: {response.status_code}")
            return

        data = response.json()
        alle_rader = []

        for obj in data.get('objekter', []):
            try:
                # 1. Koordinater
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]

                # 2. Finn fartsgrense via relasjon
                fart = "80" 
                
                # Sjekker både foreldre og barn for sikkerhets skyld
                rel_data = obj.get('relasjoner', {})
                for rel_type in ['foreldre', 'barn']:
                    for rel in rel_data.get(rel_type, []):
                        # Se etter Fartsgrense (105)
                        if rel.get('type', {}).get('id') == 105:
                            v_obj = rel.get('vegobjekt')
                            if v_obj:
                                for e in v_obj.get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])
            except:
                continue

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"Suksess! Lagret {len(alle_rader)} rader.")
        print(f"Fartsgrenser funnet i utvalget: {set([r[3] for r in alle_rader])}")

    except Exception as e:
        print(f"Feil: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
