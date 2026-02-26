import requests
import csv
import re

def hent_norske_fotobokser():
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    # 1. HENT ALLE FARTSGRENSER (105) - MED PAGINERING
    print("Henter ALLE fartsgrenser i hele Norge (dette kan ta 10-20 sekunder)...")
    fart_dict = {}
    fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
    fart_params = {'inkluder': 'egenskaper,vegsegmenter', 'srid': '4326', 'antall': 1000}
    
    try:
        while fart_url:
            res = requests.get(fart_url, params=fart_params, headers=headers)
            if res.status_code != 200: break
            
            data = res.json()
            for obj in data.get('objekter', []):
                fart_verdi = "80"
                for e in obj.get('egenskaper', []):
                    if e.get('id') == 2021:
                        fart_verdi = str(e.get('verdi'))
                
                for seg in obj.get('vegsegmenter', []):
                    vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                    fra_m = seg.get('fra_meter')
                    til_m = seg.get('til_meter')
                    
                    if vref and fra_m is not None and til_m is not None:
                        vei_nokkel = f"{vref.get('vegkategori')}{vref.get('nummer')}"
                        if vei_nokkel not in fart_dict:
                            fart_dict[vei_nokkel] = []
                        fart_dict[vei_nokkel].append({'fra': fra_m, 'til': til_m, 'fart': fart_verdi})
            
            # Sjekk om det er flere sider med data
            fart_url = data.get('metadata', {}).get('neste', {}).get('href')
            fart_params = None # Parametere ligger allerede i 'neste'-URLen

        print(f"Suksess! Lastet ned fartsgrenser for {len(fart_dict)} unike veier.")

        # 2. HENT ALLE FOTOBOKSER
        alle_rader = []
        for o_type in ["103", "823"]:
            print(f"Henter type {o_type}...")
            url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
            res = requests.get(url, params={'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}, headers=headers)
            
            if res.status_code == 200:
                for obj in res.json().get('objekter', []):
                    try:
                        coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                        if not coords: continue
                        lon, lat = coords[0], coords[1]
                        
                        fart = "80" # Default
                        if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                            seg = obj['vegsegmenter'][0]
                            vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                            m = seg.get('fra_meter')
                            
                            if vref and m is not None:
                                v_nokkel = f"{vref.get('vegkategori')}{vref.get('nummer')}"
                                if v_nokkel in fart_dict:
                                    # Din meter-logikk:
                                    for f_seg in fart_dict[v_nokkel]:
                                        if f_seg['fra'] <= m <= f_seg['til']:
                                            fart = f_seg['fart']
                                            break
                        
                        type_id = 1 if o_type == "103" else 2
                        alle_rader.append([type_id, lat, lon, fart])
                    except: continue

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
        
        print(f"Suksess! Lagret {len(alle_rader)} rader.")
        print(f"Fartsgrenser funnet i ATK.csv: {set([r[3] for r in alle_rader])}")

    except Exception as e:
        print(f"FEIL: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
