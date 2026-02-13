import requests
import csv

def hent_alle_atk():
    # Vi går tilbake til den fungerende v3-hosten
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain"
    }
    
    # Parametere som vi vet fungerer på v3
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'antall': '1000' # Henter alle i ett jafs hvis mulig
    }
    
    print(f"Kontakter: {url}")
    response = requests.get(url, params=params, headers=headers)
    print(f"Statuskode: {response.status_code}")

    if response.status_code != 200:
        print(f"Feil: {response.text}")
        return

    data = response.json()
    
    # Robust sjekk for v3-struktur (kan være liste eller dict)
    if isinstance(data, dict):
        objekter = data.get('objekter', [])
    else:
        objekter = data

    print(f"Antall objekter funnet: {len(objekter)}")

    liste = []
    for obj in objekter:
        try:
            # Hent WKT fra geometri
            geometri = obj.get('geometri', {})
            wkt = geometri.get('wkt', '')
            
            if 'POINT' in wkt:
                # Rens: "POINT (10.123 59.123)" -> ["10.123", "59.123"]
                p = wkt.replace('POINT (', '').replace(')', '').split()
                lon, lat = p[0], p[1]
                
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
            print(f"Suksess! Lagret {len(liste)} rader til ATK.csv")
        else:
            # Sikring så fila aldri er tom
            writer.writerow(['error', 'no_data', '0', '0'])
            print("Advarsel: Listen var tom.")

if __name__ == "__main__":
    hent_alle_atk()
