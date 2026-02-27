import requests
import csv
import re

def hent_norske_fotobokser():
    print("Genererer komplett ATK-datasett (Fart, Retning, Meter)...")
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_rader = []
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=30)
            if res.status_code != 200: continue
                
            for obj in res.json().get('objekter', []):
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                
                fart = "80"
                retning = "MED"
                meter = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    segment = obj['vegsegmenter'][0]
                    vls_id = segment.get('veglenkesekvensid')
                    retning = segment.get('retning', 'MED').upper()
                    meter = segment.get('fra_meter', 0)
                    
                    # Finn farten via VeglenkesekvensID (Tabell 105)
                    if vls_id:
                        f_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        f_res = requests.get(f_url, params={'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            if f_data.get('objekter'):
                                for e in f_data['objekter'][0].get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                type_id = 1 if obj_type == "103" else 2
                # Kolonner: [TYPE, LAT, LON, FART, RETNING, METER]
                alle_rader.append([type_id, coords[1], coords[0], fart, retning, int(meter)])
                
        except Exception as e:
            print(f"Feil: {e}")

    # Lagre fila
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
            
    print(f"Suksess! Lagret {len(alle_rader)} rader i ATK.csv.")
    print("Data-format: [Type, Lat, Lon, Fart, Retning, Meter]")

if __name__ == "__main__":
    hent_norske_fotobokser()
