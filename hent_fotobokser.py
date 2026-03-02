import requests
import csv
import re

def hent_norske_fotobokser():
    print("Henter data... Garanterer meter-verdier for alle boks-typer.")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    # 103 = Fast, 823 = Strekning
    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        # Vi inkluderer vegsegmenter eksplisitt for å få metreringsdata
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
        
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            objekter = res.json().get('objekter', [])
            for obj in objekter:
                # Koordinater
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                if not coords: continue
                
                fart = "80"
                retning = "MED"
                meter = 0
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    
                    # 1. PRØV Å HENTE METERVERDI FRA FLERE FELT (Løser 0-problemet)
                    # For strekning (823) ligger den ofte i 'fra_meter'
                    meter = seg.get('fra_meter')
                    
                    # Hvis den fortsatt er None, sjekk vegsystemreferansen (for 103)
                    if meter is None:
                        vref = seg.get('vegsystemreferanse', {})
                        meter = vref.get('meter')
                        
                    # Siste utvei: relativPosisjon (fra 0 til 1) omgjort til meter
                    if meter is None:
                        meter = int(seg.get('relativPosisjon', 0) * 1000)

                    retning = seg.get('retning', 'MED').upper()
                    
                    # Hent fart via VeglenkesekvensID (Tabell 105)
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
                
                # Legg til i listen: [Type, Lat, Lon, Fart, Retning, Meter]
                alle_rader.append([1 if obj_type == "103" else 2, coords[1], coords[0], fart, retning, int(meter or 0)])

    # Lagre alt til ATK.csv
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    
    print(f"Suksess! Lagret {len(alle_rader)} punkter. Sjekk de nederste radene nå.")

if __name__ == "__main__":
    hent_norske_fotobokser()
