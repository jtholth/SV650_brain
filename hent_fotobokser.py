import requests
import csv
import re

def hent_norske_fotobokser():
    print("Starter synkronisering basert på din meter-logikk (V4 Fast)...")
    
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    # Vi henter én og én type for å unngå 404-problemet med komma i URL
    objekttyper = ["103", "823"]
    alle_rader = []

    for o_type in objekttyper:
        print(f"Henter objekttype {o_type}...")
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
        params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}

        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Kunne ikke hente {o_type}: {response.status_code}")
                continue

            objekter = response.json().get('objekter', [])
            for obj in objekter:
                try:
                    # 1. Koordinater
                    wkt = obj['geometri']['wkt']
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                    lon, lat = coords[0], coords[1]

                    # 2. Hent meter-detaljer
                    fart = "80"
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        seg = obj['vegsegmenter'][0]
                        vref = seg.get('vegsystemreferanse', {}).get('kortform', '')
                        
                        # Regex for å splitte f.eks "EV6 S1D1 m1200"
                        match = re.search(r"(.*)\s+m(\d+)", vref)
                        if match:
                            vei_id = match.group(1).strip()
                            meter_punkt = int(match.group(2))

                            # 3. SØK I 105 (Fartsgrense) for denne veien
                            fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                            f_params = {'vegsystemreferanse': vei_id, 'inkluder': 'egenskaper,vegsegmenter'}
                            
                            f_res = requests.get(fart_url, params=f_params, headers=headers)
                            if f_res.status_code == 200:
                                for f_obj in f_res.json().get('objekter', []):
                                    for f_seg in f_obj.get('vegsegmenter', []):
                                        myyy = f_seg.get('fra_meter')
                                        mzzz = f_seg.get('til_meter')
                                        
                                        # DIN LOGIKK: Er m485 mellom myyy og mzzz?
                                        if myyy <= meter_punkt <= mzzz:
                                            for e in f_obj.get('egenskaper', []):
                                                if e.get('id') == 2021:
                                                    fart = str(e.get('verdi'))
                                                    break
                                    if fart != "80": break

                    type_id = 1 if o_type == "103" else 2
                    alle_rader.append([type_id, lat, lon, fart])
                except:
                    continue
        except Exception as e:
            print(f"Feil: {e}")

    # Lagre fila
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
            
    print(f"FERDIG! Fant fartsgrenser: {set([r[3] for r in alle_rader])}")

if __name__ == "__main__":
    hent_norske_fotobokser()
