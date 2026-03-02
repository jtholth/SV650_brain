import requests
import csv
import re

def beregn_varslingsavstand(fartsgrense_str):
    try:
        fart = int(fartsgrense_str)
        # Vi vil ha varsel ca 30 sekunder før (fart / 3.6 * 30)
        # Vi runder av til nærmeste 50 meter for ryddighet
        avstand = (fart / 3.6) * 30
        return int(round(avstand / 50.0) * 50.0)
    except:
        return 600 # Fallback hvis fart mangler

def hent_norske_fotobokser():
    print("Henter data med variabel varslingsavstand basert på fart...")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
        res = requests.get(url, params=params, headers=headers)
        
        if res.status_code == 200:
            for obj in res.json().get('objekter', []):
                coords = re.findall(r"[-+]?\d*\.?\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]
                
                fart = "80"
                retning = "MED"
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    retning = seg.get('retning', 'MED').upper()
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
                
                # NÅ SETTER VI VARIABEL AVSTAND I SISTE KOLONNE
                varsel_meter = beregn_varslingsavstand(fart)
                
                # Type 1 = Fast, Type 2 = Strekning
                t = 1 if obj_type == "103" else 2
                alle_rader.append([t, lat, lon, fart, retning, varsel_meter])

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    print(f"Ferdig! Sjekk ATK.csv – nå er meter-kolonnen dynamisk etter fartsgrensen.")

if __name__ == "__main__":
    hent_norske_fotobokser()
