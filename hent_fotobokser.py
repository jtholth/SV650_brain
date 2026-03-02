import requests
import csv
import re

def hent_norske_fotobokser():
    print("Synkroniserer... Henter meterverdier fra vegsystemreferanse.")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            objekter = res.json().get('objekter', [])
            for obj in objekter:
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                
                fart = "80"
                retning = "MED"
                meter = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    
                    # 1. Prøv å hente meter fra vegsystemreferanse (standard i V4)
                    vref = seg.get('vegsystemreferanse', {})
                    meter = vref.get('meter', 0)
                    
                    # 2. Hvis fortsatt 0, prøv relativPosisjon (og gjør om til meter)
                    if meter == 0:
                        rel_pos = seg.get('relativPosisjon', 0)
                        meter = int(rel_pos * 1000) if rel_pos > 0 else 0
                    
                    retning = seg.get('retning', 'MED').upper()
                    
                    # Hent fart (din vinner-metode)
                    vls_id = seg.get('veglenkesekvensid')
                    if vls_id:
                        f_res = requests.get(f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105", 
                                             params={'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            if f_data.get('objekter'):
                                for e in f_data['objekter'][0].get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                alle_rader.append([1 if obj_type == "103" else 2, coords[1], coords[0], fart, retning, int(meter)])

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    
    print(f"Ferdig! Lagret {len(alle_rader)} rader. Sjekk de nederste radene i fila nå.")

if __name__ == "__main__":
    hent_norske_fotobokser()
