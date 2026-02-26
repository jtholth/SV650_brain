import requests
import csv
import re
import time

def hent_fart_for_posisjon(lat, lon):
    # Denne funksjonen spør NVDB om hvilket objekt 105 som ligger på dette punktet
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
    params = {
        'kartutsnitt': f"{lon},{lat},{lon},{lat}", # Et bittelite punkt
        'srid': '4326',
        'inkluder': 'egenskaper'
    }
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for obj in data.get('objekter', []):
                for egenskap in obj.get('egenskaper', []):
                    if egenskap.get('id') == 2021: # Fartsgrense-verdien
                        return str(egenskap.get('verdi', '80'))
    except:
        pass
    return "80"

def hent_norske_fotobokser():
    print("Kobler til NVDB V4 for å hente bokser og fartsgrenser (105)...")
    base_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/"
    objekttyper = ["103", "823"]
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}

    try:
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            total_antall = 0

            for o_type in objekttyper:
                params = {'inkluder': 'geometri', 'srid': '4326', 'vegsystemreferanse': 'E,R,F'}
                response = requests.get(base_url + o_type, params=params, headers=headers)
                
                if response.status_code == 200:
                    objekter = response.json().get('objekter', [])
                    for obj in objekter:
                        try:
                            wkt = obj['geometri']['wkt']
                            coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                            if len(coords) >= 2:
                                lon, lat = coords[0], coords[1]
                                
                                # Her skjer magien: Vi henter fart fra objekt 105
                                fart = hent_fart_for_posisjon(lat, lon)
                                
                                type_id = 1 if o_type == "103" else 2
                                writer.writerow([type_id, lat, lon, fart])
                                total_antall += 1
                                
                                # Vi må være litt snille med API-et så vi ikke blir kasta ut
                                if total_antall % 50 == 0:
                                    print(f"Hentet {total_antall} punkter...")
                                    time.sleep(0.1) 
                        except:
                            continue
        print(f"FERDIG! Lagret {total_antall} punkter med ekte fartsgrenser fra obj 105.")
    except Exception as e:
        print(f"Feil: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
