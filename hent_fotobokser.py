import requests
import csv
import re

def hent_norske_fotobokser():
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    # 1. HENT ALLE FARTSGRENSER (105)
    print("Henter alle fartsgrenser i Norge (105)...")
    fart_dict = {}
    fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
    fart_params = {'inkluder': 'egenskaper,vegsegmenter', 'srid': '4326'}
    
    try:
        f_res = requests.get(fart_url, params=fart_params, headers=headers)
        if f_res.status_code == 200:
            for obj in f_res.json().get('objekter', []):
                fart_verdi = "80"
                for e in obj.get('egenskaper', []):
                    if e.get('id') == 2021:
                        fart_verdi = str(e.get('verdi'))
                
                for seg in obj.get('vegsegmenter', []):
                    vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                    # SJEKK: Har vi både vei-info og meter-info?
                    fra_m = seg.get('fra_meter')
                    til_m = seg.get('til_meter')
                    
                    if vref and fra_m is not None and til_m is not None:
                        vei_nokkel = f"{vref.get('vegkategori')}{vref.get('nummer')}"
                        if vei_nokkel not in fart_dict:
                            fart_dict[vei_nokkel] = []
                        fart_dict[vei_nokkel].append({
                            'fra': fra_m,
                            'til': til_m,
                            'fart': fart_verdi
                        })
        print(f"Lastet ned fartsgrenser for {len(fart_dict)} veier.")

        # 2. HENT ALLE FOTOBOKSER
        alle_rader = []
        for o_type in ["103", "823"]:
            print(f"Henter type {o_type}...")
            url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
            res = requests.get(url, params={'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}, headers=headers)
            
            if res.status_code == 200:
                for obj in res.json().get('objekter', []):
                    try:
                        # Koordinater
                        coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                        if not coords: continue
                        lon, lat = coords[0], coords[1]
                        
                        fart = "80"
                        if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                            seg = obj['vegsegmenter'][0]
                            vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                            m = seg.get('fra_meter')
                            
                            if vref and m is not None:
                                v_nokkel = f"{vref.get('vegkategori')}{vref.get('nummer')}"
                                if v_nokkel in fart_dict:
                                    for f_seg in fart_dict[v_nokkel]:
                                        # DIN LOGIKK med sikkerhetssjekk
                                        if f_seg['fra'] <= m <= f_seg['til']:
                                            fart = f_seg['fart']
                                            break
                        
                        type_id = 1 if o_type == "103" else 2
                        alle_rader.append([type_id, lat, lon, fart])
                    except:
                        continue

        # 3. LAGRE FILA
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
        
        print(f"Suksess! Lagret {len(alle_rader)} rader i ATK.csv.")
        print(f"Unike farter funnet: {set([r[3] for r in alle_rader])}")

    except Exception as e:
        print(f"FEIL: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
