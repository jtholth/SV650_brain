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
                            # Vi bruker "Regex" for å trekke ut kun tallene fra POINT eller LINESTRING
                            coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                            
                            if len(coords) >= 2:
                                lon = coords[0]
                                lat = coords[1]
                                
                                # Finn fartsgrense
                                fart = 80
                                for egenskap in obj.get('egenskaper', []):
                                    if "fartsgrense" in egenskap.get('navn', '').lower():
                                        fart = egenskap.get('verdi', 80)
                                
                                # Lagrer rent: Type, Lat, Lon, Fart
                                writer.writerow([final_type, lat, lon, fart])
                                total_antall += 1
                        except Exception as e:
                            continue
                else:
                    print(f"Kunne ikke hente {o_type}: {response.status_code}")

        print(f"FERDIG! Lagret {total_antall} rene punkter i 'ATK.csv'.")
        
    except Exception as e:
        print(f"En feil oppstod: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
