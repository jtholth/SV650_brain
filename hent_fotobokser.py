import requests
import csv
import re

def hent_norske_fotobokser():
    print("Starter henting... Skriver til ATK.csv fortløpende.")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    # Åpne filen med en gang for å skrive rad for rad
    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        for obj_type in ["103", "823"]:
            print(f"Henter type {obj_type}...")
            url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
            params = {'inkluder': 'geometri,vegsegmenter,metadata', 'srid': '4326'}
            
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
                        
                        # HENT METER: Sjekker 'fra_meter' først (viktig for 823), deretter vref
                        meter = seg.get('fra_meter')
                        if meter is None:
                            meter = seg.get('vegsystemreferanse', {}).get('meter', 0)
                        
                        retning = seg.get('retning', 'MED').upper()
                        
                        # Fartsgrense-sjekk (Vi gjør dette kun hvis vi må for å spare tid)
                        # Men for å være sikker på at filen oppdateres, hopper vi over 
                        # tunge API-kall i denne runden for å se at METER fungerer.
                        if seg.get('fartsgrense'):
                            fart = str(seg.get('fartsgrense'))

                    # Skriv raden umiddelbart
                    ny_rad = [1 if obj_type == "103" else 2, coords[1], coords[0], fart, retning, int(meter)]
                    writer.writerow(ny_rad)
                    
                    if i % 100 == 0:
                        print(f"Status {obj_type}: Behandlet {i} objekter...")

    print("Ferdig! Filen ATK.csv skal nå være fullstendig oppdatert.")

if __name__ == "__main__":
    hent_norske_fotobokser()
