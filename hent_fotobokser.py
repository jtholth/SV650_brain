import requests
import csv

def hent_alle_atk():
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain"
    }
    params = {'inkluder': 'egenskaper,geometri', 'srid': '4326'}
    
    print("Henter data fra NVDB...")
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Kunne ikke hente data: {e}")
        data = []

    if isinstance(data, list):
        objekter = data
    elif isinstance(data, dict):
        objekter = data.get('objekter', [])
    else:
        objekter = []

    liste = []
    for obj in objekter:
        try:
            wkt = obj['geometri']['wkt']
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

    # VIKTIG: Vi lager fila UANSETT om den er tom eller ikke
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"Suksess! Lagret {len(liste)} rader.")
        else:
            print("Ingen data funnet, laget tom fil for å unngå feil.")

if __name__ == "__main__":
    hent_alle_atk()
