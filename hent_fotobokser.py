import requests
import csv
import re

def hent_norske_fotobokser():
    print("Synkroniserer med NVDB V4... Henter faste og streknings-ATK.")
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    alle_rader = []
    # Vi henter 103 (Fast) og 823 (Strekning)
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=30)
            if res.status_code != 200: continue
                
            for obj in res.json().get('objekter', []):
                # 1. Hent koordinater
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]
                
                fart = "80"
                retning = "MED"
                meter_verdi = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    
                    # 2. Hent METER (Denne gangen fra vegsystemreferanse)
                    vref = seg.get('vegsystemreferanse', {})
                    meter_verdi = vref.get('meter', 0)
                    
                    # 3. Hent RETNING (Arvet fra 775)
                    retning = seg.get('retning', 'MED').upper()
                    
                    # 4. Hent FART via VeglenkesekvensID (Din metode)
                    vls_id = seg.get('veglenkesekvensid')
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
                alle_rader.append([type_id, lat, lon, fart, retning, int(meter_verdi)])
                
        except Exception as e:
            print(f"Kunne ikke hente type {obj_type}: {e}")

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
            
    print(f"Ferdig! Lagret {len(alle_rader)} rader i ATK.csv.")

if __name__ == "__main__":
    hent_norske_fotobokser()
