import requests
import csv

def hent_alle_atk():
    # Start-URL
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain-Project"
    }
    
    # Start-parametre
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false',
        'antall': '100' # Henter 100 av gangen
    }
    
    liste = []
    neste_url = url
    besøkte_urls = set()
    
    print("Starter henting fra NVDB API V4...")
    
    while neste_url and neste_url not in besøkte_urls:
        try:
            besøkte_urls.add(neste_url)
            
            # Viktig: Bruk params KUN på den aller første forespørselen.
            # 'neste_url' fra metadata inneholder allerede alle parametere.
            if len(besøkte_urls) == 1:
                response = requests.get(neste_url, params=params, headers=headers)
            else:
                response = requests.get(neste_url, headers=headers)
            
            if response.status_code != 200:
                print(f"Stoppet. Status: {response.status_code}")
                break
                
            data = response.json()
            objekter = data.get('objekter', [])
            
            if not objekter:
                break

            for obj in objekter:
                try:
                    geometri = obj.get('geometri', {})
                    wkt = geometri.get('wkt', '')
                    if 'POINT' in wkt:
                        coords = wkt.replace('POINT (', '').replace(')', '').split()
                        lon, lat = coords[0], coords[1]
                        
                        type_atk, retning = 1, 0
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
            
            print(f"Hentet totalt {len(liste)} fotobokser så langt...")

            # Finn neste side i metadata
            metadata = data.get('metadata', {})
            neste_info = metadata.get('neste', {})
            neste_url = neste_info.get('href')
            
            # Sikkerhetsventil: Norge har ca 450-500 fotobokser. 
            # Hvis vi passerer 1000, er det noe galt.
            if len(liste) > 1000:
                print("Sikkerhetsventil utløst (for mange objekter).")
                break
                
        except Exception as e:
            print(f"Feil: {e}")
            break

    # Lagre til fil
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"FERDIG! Lagret {len(liste)} unike rader til ATK.csv")
        else:
            writer.writerow(['error', '0', '0', '0'])

if __name__ == "__main__":
    hent_alle_atk()
