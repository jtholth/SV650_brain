import requests
import csv
import re

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB V4)...")
    
    base_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/"
    objekttyper = ["103", "823"] 
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-Project'
    }

    try:
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            total_antall = 0

            for o_type in objekttyper:
                print(f"Henter objekttype {o_type}...")
                params = {
                    'inkluder': 'egenskaper,geometri,metadata', # Lagt til metadata
                    'srid': '4326',
                    'vegsystemreferanse': 'E,R,F'
                }

                response = requests.get(base_url + o_type, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    for obj in data.get('objekter', []):
                        final_type = 1 if o_type == "103" else 2
                        
                        try:
                            wkt = obj['geometri']['wkt']
                            coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                            
                            if len(coords) >= 2:
                                lon = coords[0]
                                lat = coords[1]
                                
                                # --- NY OG BEDRE FARTS-SJEKK ---
                                fart = "80" 
                                egenskap_liste = obj.get('egenskaper', [])
                                
                                # Vi leter spesifikt etter ID 2021 (Fartsgrense)
                                for e in egenskap_liste:
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi', '80'))
                                        break
                                    # Backup: se etter ordet fartsgrense i navnet
                                    elif "fartsgrense" in str(e.get('navn', '')).lower():
                                        fart = str(e.get('verdi', '80'))
                                        break
                                
                                # Rens ut alt som ikke er tall (f.eks "70 (km/t)" -> "70")
                                fart = "".join(filter(str.isdigit, fart))
                                if not fart: fart = "80"

                                writer.writerow([final_type, lat, lon, fart])
                                total_antall += 1
                        except:
                            continue
                else:
                    print(f"Feil ved henting: {response.status_code}")

        print(f"FERDIG! Lagret {total_antall} punkter.")
        
    except Exception as e:
        print(f"En feil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
