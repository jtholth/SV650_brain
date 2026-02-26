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
                    'inkluder': 'egenskaper,geometri',
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
                                
                                # BEDRE FARTS-SJEKK
                                fart = "80" # Default hvis alt feiler
                                for egenskap in obj.get('egenskaper', []):
                                    navn = egenskap.get('navn', '').lower()
                                    # Sjekker etter "fartsgrense" eller ID 2021
                                    if "fartsgrense" in navn or egenskap.get('id') == 2021:
                                        verdi = egenskap.get('verdi')
                                        if verdi:
                                            # Trekker ut kun tallene (f.eks "80 (km/t)" blir "80")
                                            fart_match = re.search(r'\d+', str(verdi))
                                            if fart_match:
                                                fart = fart_match.group()
                                
                                writer.writerow([final_type, lat, lon, fart])
                                total_antall += 1
                        except:
                            continue
                else:
                    print(f"Feil ved henting: {response.status_code}")

        print(f"FERDIG! Lagret {total_antall} punkter i 'ATK.csv'.")
        
    except Exception as e:
        print(f"En feil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
