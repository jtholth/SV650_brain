import requests
import csv
import re

def hent_norske_fotobokser():
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    # --- STEG 1: BYGG OPP "REGNEARKET" FOR FARTSGRENSER (105) ---
    print("Bygger oppslagsliste for fartsgrenser (105)...")
    fart_oppslag = {} # Dette er "regnearket" vårt
    
    neste_side = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105?inkluder=vegsegmenter,egenskaper&srid=4326&antall=1000"
    
    while neste_side:
        res = requests.get(neste_side, headers=headers)
        if res.status_code != 200: break
        data = res.json()
        
        for obj in data.get('objekter', []):
            # Finn fart-verdien (Egenskap 2021)
            fart_verdi = "80"
            for e in obj.get('egenskaper', []):
                if e.get('id') == 2021:
                    fart_verdi = str(e.get('verdi'))
            
            # Legg inn i "regnearket" basert på veisystem og meter
            for seg in obj.get('vegsegmenter', []):
                vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                if vref:
                    # Lag navnet (f.eks "F301 S1D1")
                    v_kat = vref.get('vegkategori')
                    v_nr = vref.get('nummer')
                    v_strekning = vref.get('strekning', '')
                    v_delstrekning = vref.get('delstrekning', '')
                    
                    vei_navn = f"{v_kat}{v_nr} S{v_strekning}D{v_delstrekning}"
                    
                    if vei_navn not in fart_oppslag:
                        fart_oppslag[vei_navn] = []
                    
                    fart_oppslag[vei_navn].append({
                        'yyy': seg.get('fra_meter'),
                        'zzz': seg.get('til_meter'),
                        'fart': fart_verdi
                    })
        
        neste_side = data.get('metadata', {}).get('neste', {}).get('href')
        print(f"Laster ned... (veier i minnet: {len(fart_oppslag)})")

    # --- STEG 2: HENT ATK OG KJØR SAMMENLIGNINGEN ---
    print("\nStarter matching av ATK mot fartsgrenser...")
    alle_rader = []
    
    for o_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{o_type}?inkluder=geometri,vegsegmenter,metadata&srid=4326"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            for obj in res.json().get('objekter', []):
                try:
                    coords = re.findall(r"[-+]?\d*\.\d+|\d+", obj['geometri']['wkt'])
                    lon, lat = coords[0], coords[1]
                    
                    fart = "80" # Standard
                    if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                        seg = obj['vegsegmenter'][0]
                        vref = seg.get('vegsystemreferanse', {}).get('vegsystem', {})
                        
                        # Finn boksens Navn og XXX (meter)
                        v_kat = vref.get('vegkategori')
                        v_nr = vref.get('nummer')
                        v_strekning = vref.get('strekning', '')
                        v_delstrekning = vref.get('delstrekning', '')
                        
                        atk_vei_navn = f"{v_kat}{v_nr} S{v_strekning}D{v_delstrekning}"
                        xxx = seg.get('fra_meter')
                        
                        # LET OPP I REGNEARKET (Steg 3 i din logikk)
                        if atk_vei_navn in fart_oppslag:
                            for rad in fart_oppslag[atk_vei_navn]:
                                if rad['yyy'] <= xxx <= rad['zzz']:
                                    fart = rad['fart']
                                    break
                    
                    type_id = 1 if o_type == "103" else 2
                    alle_rader.append([type_id, lat, lon, fart])
                except: continue

    # --- STEG 4: LAGRE FILA ---
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    
    print(f"\nFERDIG! Lagret {len(alle_rader)} rader.")
    print(f"Fant disse fartsgrensene: {set([r[3] for r in alle_rader])}")

if __name__ == "__main__":
    hent_norske_fotobokser()
