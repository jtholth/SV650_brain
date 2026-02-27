import requests
import csv
import re

def hent_norske_fotobokser():
    print("Følger din oppskrift: Kobler via VeglenkesekvensID...")
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_rader = []
    # Vi henter 103 og 823
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=30)
            if res.status_code != 200: continue
                
            objekter = res.json().get('objekter', [])
            for obj in objekter:
                # 1. Hent koordinater
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]
                
                # 2. FINN VEGLENKESEKVENSID (Din kjerne-ID)
                fart = "80"
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    segment = obj['vegsegmenter'][0]
                    vls_id = segment.get('veglenkesekvensid')
                    
                    if vls_id:
                        # 3. GÅ TIL TABELL 105 og finn match på denne VLS-ID
                        fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        # Vi filtrerer på den spesifikke veglenkesekvensen vi akkurat fant
                        fart_params = {
                            'veglenkesekvens': vls_id,
                            'inkluder': 'egenskaper',
                            'srid': '4326'
                        }
                        
                        f_res = requests.get(fart_url, params=fart_params, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            # Hvis vi finner fartsgrenser på denne lenken
                            if f_data.get('objekter'):
                                # Vi henter egenskap 2021
                                for e in f_data['objekter'][0].get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                type_id = 1 if obj_type == "103" else 2
                alle_rader.append([type_id, lat, lon, fart])
                
        except Exception as e:
            print(f"Feil: {e}")

    # Lagre til ATK.csv
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
            
    print(f"Ferdig! Lagret {len(alle_rader)} rader.")
    print(f"Fartsgrenser funnet med din metode: {set([r[3] for r in alle_rader])}")

if __name__ == "__main__":
    hent_norske_fotobokser()
