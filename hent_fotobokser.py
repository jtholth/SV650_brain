import requests
import csv
import re

def hent_norske_fotobokser():
    print("Starter synkronisering basert på din meter-logikk...")
    
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    atk_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}

    try:
        response = requests.get(atk_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Feil ved henting av ATK: {response.status_code}")
            return

        objekter = response.json().get('objekter', [])
        alle_rader = []

        for obj in objekter:
            try:
                # 1. Koordinater
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                lon, lat = coords[0], coords[1]

                # 2. Hent meter-detaljer fra ATK-en
                fart = "80" # Default hvis vi ikke finner treff
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    segment = obj['vegsegmenter'][0]
                    
                    # Her henter vi 'vegsystemreferanse' (f.eks. FV301 S1D1) og 'fra_meter'
                    vref = segment.get('vegsystemreferanse', {})
                    veinavn = vref.get('kortform', '') # F.eks "EV6 S1D1"
                    
                    # Vi bruker regex for å skille veien fra meteren (f.eks "EV6 S1D1 m1200" -> "EV6 S1D1" og 1200)
                    match = re.match(r"(.*)\s+m(\d+)", veinavn)
                    if match:
                        vei_id = match.group(1)
                        meter_punkt = int(match.group(2))
                        
                        # 3. SØK I 105 for denne spesifikke veien
                        fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        fart_params = {
                            'vegsystemreferanse': vei_id,
                            'inkluder': 'egenskaper,vegsegmenter'
                        }
                        
                        f_res = requests.get(fart_url, params=fart_params, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            for f_obj in f_data.get('objekter', []):
                                for f_seg in f_obj.get('vegsegmenter', []):
                                    myyy = f_seg.get('fra_meter')
                                    mzzz = f_seg.get('til_meter')
                                    
                                    # DIN LOGIKK: Sjekk om meter_punkt er mellom myyy og mzzz
                                    if myyy <= meter_punkt <= mzzz:
                                        # Finn fartsgrense-egenskapen (ID 2021)
                                        for e in f_obj.get('egenskaper', []):
                                            if e.get('id') == 2021:
                                                fart = str(e.get('verdi'))
                                                break
                                if fart != "80": break # Avbryt hvis vi fant farten

                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])
            except:
                continue

        # Lagre til fila
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"Fullført! Fant følgende unike fartsgrenser: {set([r[3] for r in alle_rader])}")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
