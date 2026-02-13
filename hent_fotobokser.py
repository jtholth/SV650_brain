import requests
import csv

def hent_alle_atk():
    # Korrekt V4 URL i henhold til nyeste dokumentasjon
    base_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain-Project"
    }
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    liste = []
    neste_url = base_url
    
    print("Starter henting fra NVDB API V4...")
    
    while neste_url:
        try:
            # Vi bruker params kun på første forespørsel, 'neste' URL inneholder alt
            response = requests.get(neste_url, params=params if neste_url == base_url else None, headers=headers)
            
            if response.status_code != 200:
                print(f"Feil: {response.status_code}")
                break
                
            data = response.json()
            objekter = data.get('objekter', [])
            
            for obj in objekter:
                try:
                    # Geometri
                    wkt = obj.get('geometri', {}).get('wkt', '')
                    if 'POINT' in wkt:
                        coords = wkt.replace('POINT (', '').replace(')', '').split()
                        lon, lat = coords[0], coords[1]
                        
                        type_atk, retning = 1, 0
                        # Egenskaper
                        for eg in obj.get('egenskaper', []):
                            navn = eg.get('navn', '')
                            verdi = str(eg.get('verdi', ''))
                            if 'Type' in navn and 'Strekning' in verdi: type_atk = 2
                            if 'retning' in navn.lower():
                                if 'Med' in verdi: retning = 1
                                elif 'Mot' in verdi: retning = 2
                        
                        liste.append([lat, lon, retning, type_atk])
                except:
                    continue
            
            # Paginering: Finn neste side
            neste_metadata = data.get('metadata', {}).get('neste', {})
            neste_url = neste_metadata.get('href')
            print(f"Hentet {len(liste)} fotobokser...")
            
        except Exception as e:
            print(f"Feil underveis: {e}")
            break

    # Skriv til fil
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"FERDIG! Lagret totalt {len(liste)} rader til ATK.csv")
        else:
            writer.writerow(['error', '0', '0', '0'])
            print("Kunne ikke finne data.")

if __name__ == "__main__":
    hent_alle_atk()
