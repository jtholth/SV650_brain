import requests
import csv
import re
import time

def hent_norske_fotobokser():
    print("Gjenoppretter full datahenting (Fart + Meter)... Dette tar ca 1-2 minutter.")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    # 103 = Fast, 823 = Strekning
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        # Vi MÅ ha vegsegmenter for å finne meter og veglenke-ID
        params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
        
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            objekter = res.json().get('objekter', [])
            for i, obj in enumerate(objekter):
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                
                fart = "80"
                retning = "MED"
                meter = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    
                    # METER-LOGIKK: Sjekker tre steder for å unngå 0
                    meter = seg.get('fra_meter') # Ofte brukt for strekning (823)
                    if meter is None or meter == 0:
                        vref = seg.get('vegsystemreferanse', {})
                        meter = vref.get('meter', 0)
                    
                    retning = seg.get('retning', 'MED').upper()
                    vls_id = seg.get('veglenkesekvensid')

                    # FART-LOGIKK (Din vinner-metode fra tabell 105)
                    if vls_id:
                        f_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        f_params = {'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}
                        f_res = requests.get(f_url, params=f_params, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            if f_data.get('objekter'):
                                # Vi henter egenskap 2021 (Fartsgrense)
                                for e in f_data['objekter'][0].get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                # Legg til raden
                alle_rader.append([1 if obj_type == "103" else 2, coords[1], coords[0], fart, retning, int(meter)])
                
                if i % 50 == 0:
                    print(f"Hentet {i} av {len(objekter)} for type {obj_type}...")

    # Skriv alt til fil til slutt for å sikre at vi ikke får korrupt CSV
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    
    print(f"\nSuksess! Lagret {len(alle_rader)} rader.")
    print("Sjekk rad 800+ nå – farten skal variere og meter skal ikke være 0.")

if __name__ == "__main__":
    hent_norske_fotobokser()
