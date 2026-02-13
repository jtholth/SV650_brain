import requests
import csv

def hent_alle_atk():
    # Dette er den offisielle V4-adressen fra feilmeldingen din
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain-Project"
    }
    
    # Parametere for V4
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    print(f"Kobler til NVDB API V4...")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Statuskode: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API-feil: {response.text}")
            return

        data = response.json()
        
        # I V4 ligger objektene i 'objekter'
        objekter = data.get('objekter', [])
        print(f"Suksess! Fant {len(objekter)} fotobokser på denne siden.")

        liste = []
        for obj in objekter:
            try:
                # Hent koordinater
                geometri = obj.get('geometri', {})
                wkt = geometri.get('wkt', '')
                
                if 'POINT' in wkt:
                    # Rens: POINT (10.123 59.123)
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

        # Lagre til fil
        with open('ATK.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            if liste:
                writer.writerows(liste)
                print(f"Lagret {len(liste)} rader til ATK.csv")
            else:
                writer.writerow(['0', '0', '0', '0'])
                print("Ingen rader funnet.")

    except Exception as e:
        print(f"Feil: {e}")

if __name__ == "__main__":
    hent_alle_atk()
