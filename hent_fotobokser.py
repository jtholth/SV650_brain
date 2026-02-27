import requests
import csv
import re

def hent_norske_fotobokser():
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }
    
    # --- STEG 1: BYGG OPPSLAGSLISTE (105) ---
    print("Henter fartsgrenser (105)... Dette skal ta under 2 minutter.")
    fart_oppslag = {}
    
    # Vi filtrerer på vegkategori for å redusere datamengden (E, R, F)
    fart_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
    params = {
        'inkluder': 'vegsegmenter,egenskaper',
        'srid': '4326',
        'antall': 1000,
        'vegsystemreferanse': 'E,R,F' 
    }
    
    try:
        while fart_url:
            res = requests.get(fart_url, params=params, headers=headers, timeout=30)
            if res.status_code != 200: break
            data = res.json()
            
            for obj in data.get('objekter', []):
                fart_verdi = "80"
                for e in obj.get('egenskaper', []):
                    if e.get('id') == 2021:
                        fart_verdi = str(e.get('verdi'))
                
                for seg in obj.get('vegsegmenter', []):
                    vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                    if vref:
                        # Nøkkel: "F301 S1D1"
                        v_navn = f"{vref.get('vegkategori')}{vref.get('nummer')} S{vref.get('strekning')}D{vref.get('delstrekning')}"
                        if v_navn not in fart_oppslag:
                            fart_oppslag[v_navn] = []
                        
                        fart_oppslag[v_navn].append({
                            'y': seg.get('fra_meter'),
                            'z': seg.get('til_meter'),
                            'f': fart_verdi
                        })
            
            # Finn neste side
            fart_url = data.get('metadata', {}).get('neste', {}).get('href')
            params = None # Metadata-URL-en inneholder allerede parameterne
            print(f"Laster... {len(fart_oppslag)} veistrekninger i minnet", end='\r')
            
            # Sikkerhet: Hvis den har hentet over 15.000 objekter, stopper vi (unngår 7 timer)
            if len(fart_oppslag) > 15000: break

        # --- STEG 2: MATCH ATK (103, 823) ---
        print("\nMatcher ATK mot regnearket...")
        alle_rader = []
        for o_type in ["103", "823"]:
            url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}"
            res = requests.get(url, params={'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}, headers=headers)
            
            if res.status_code == 200:
                for obj in res.json().get('objekter', []):
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                    if not coords: continue
                    
                    fart = "80"
                    if 'vegsegmenter' in obj:
                        seg = obj['vegsegmenter'][0]
                        vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                        if vref:
                            # Lag samme nøkkel som i oppslaget
                            atk_v = f"{vref.get('vegkategori')}{vref.get('nummer')} S{vref.get('strekning')}D{vref.get('delstrekning')}"
                            x = seg.get('fra_meter')
                            
                            if atk_v in fart_oppslag:
                                for rad in fart_oppslag[atk_v]:
                                    if rad['y'] <= x <= rad['z']:
                                        fart = rad['f']
                                        break
                    
                    type_id = 1 if o_type == "103" else 2
                    alle_rader.append([type_id, coords[1], coords[0], fart])

        # --- STEG 3: LAGRE ---
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
        
        print(f"Ferdig! Lagret {len(alle_rader)} rader. Farter funnet: {set([r[3] for r in alle_rader])}")

    except Exception as e:
        print(f"\nFeil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
