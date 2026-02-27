import requests
import csv
import re

def hent_norske_fotobokser():
    print("Henter fotobokser med korrekt relasjons-mapping (V4)...")
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_rader = []
    # Vi henter 103 og 823 hver for seg for å være helt sikre mot 404
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        # 'inkluder=alle' er den sikreste måten å få med relasjons-data og egenskaper
        params = {
            'inkluder': 'geometri,relasjoner,metadata',
            'srid': '4326'
        }
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=30)
            if res.status_code != 200:
                continue
                
            data = res.json()
            for obj in data.get('objekter', []):
                # 1. Koordinater
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]
                
                # 2. Finn fartsgrense via 'relasjoner' -> 'foreldre'
                fart = "80"
                relasjoner = obj.get('relasjoner', {})
                foreldre = relasjoner.get('foreldre', [])
                
                for rel in foreldre:
                    # Vi leter etter relasjon til objekttype 105 (Fartsgrense)
                    if rel.get('type', {}).get('id') == 105:
                        # I V4 ligger ofte 'vegobjekt' som et nøstet objekt hvis man ber om det
                        v_obj = rel.get('vegobjekt')
                        if v_obj:
                            for e in v_obj.get('egenskaper', []):
                                if e.get('id') == 2021: # Egenskaps-ID for fartsgrense
                                    fart = str(e.get('verdi'))
                                    break
                
                type_id = 1 if obj_type == "103" else 2
                alle_rader.append([type_id, lat, lon, fart])
                
        except Exception as e:
            print(f"Feil ved type {obj_type}: {e}")

    # Lagre til fila
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
            
    print(f"Ferdig! Lagret {len(alle_rader)} rader.")
    print(f"Unike fartsgrenser funnet: {set([r[3] for r in alle_rader])}")

if __name__ == "__main__":
    hent_norske_fotobokser()
