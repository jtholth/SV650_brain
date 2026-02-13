import requests
import csv
import re

def hent_alle_atk():
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/162"
    headers = {"Accept": "application/json", "X-Client": "SV650-Brain-Project"}
    params = {'inkluder': 'egenskaper,geometri', 'srid': '4326', 'alle_versjoner': 'false', 'antall': '100'}
    
    liste = []
    neste_url = url
    besøkte_urls = set()

    while neste_url and neste_url not in besøkte_urls:
        try:
            besøkte_urls.add(neste_url)
            response = requests.get(neste_url, params=params if len(besøkte_urls)==1 else None, headers=headers)
            if response.status_code != 200: break
            
            data = response.json()
            for obj in data.get('objekter', []):
                wkt = obj.get('geometri', {}).get('wkt', '')
                # Finn alle tall (inkludert desimaler) i WKT-strengen
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1] # NVDB sender Lon, Lat
                    
                    type_atk, retning = 1, 0
                    for eg in obj.get('egenskaper', []):
                        navn = eg.get('navn', '')
                        verdi = str(eg.get('verdi', ''))
                        if 'Type' in navn and 'Strekning' in verdi: type_atk = 2
                        if 'retning' in navn.lower():
                            if 'Med' in verdi: retning = 1
                            elif 'Mot' in verdi: retning = 2
                    
                    # Lagre som: LAT, LON, RETNING, TYPE (Standard GPS format)
                    liste.append([lat, lon, retning, type_atk])
            
            neste_url = data.get('metadata', {}).get('neste', {}).get('href')
            print(f"Hentet {len(liste)} fotobokser...")
        except: break

    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(liste)
    print(f"Ferdig! Lagret {len(liste)} rader med rene koordinater.")

if __name__ == "__main__":
    hent_alle_atk()
