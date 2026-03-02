import requests
import csv
import re

def hent_norske_fotobokser():
    print("Henter data... Fikser meterverdier for streknings-ATK (fra rad 800+).")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            for obj in res.json().get('objekter', []):
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                
                fart = "80"
                retning = "MED"
                meter = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    
                    # LOGIKK FOR Å UNNGÅ 0:
                    # 1. Prøv 'fra_meter' (viktig for strekning/823)
                    meter = seg.get('fra_meter')
                    
                    # 2. Hvis None, prøv vegsystemreferanse (standard for punkt/103)
                    if meter is None:
                        vref = seg.get('vegsystemreferanse', {})
                        meter = vref.get('meter')
                    
                    # 3. Fallback til relativPosisjon
                    if meter is None:
                        meter = seg.get('relativPosisjon', 0) * 1000

                    retning = seg.get('retning', 'MED').upper()
                    vls_id = seg.get('veglenkesekvensid')
                    
                    # Hent fartsgrense (din vinner-metode)
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
                
                alle_rader.append([1 if obj_type == "103" else 2, coords[1], coords[0], fart, retning, int(meter or 0)])

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    print(f"Ferdig! Sjekk rad 800+ nå. Ingen skal være 0.")

if __name__ == "__main__":
    hent_norske_fotobokser()
