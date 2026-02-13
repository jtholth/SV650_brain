import requests
import csv

def hent_alle_atk():
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain-Project"
    }
    params = {'inkluder': 'egenskaper,geometri', 'srid': '4326'}
    
    print("Henter data fra NVDB...")
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    # Her håndterer vi listen direkte uten å bruke .get()
    if isinstance(data, list):
        objekter = data
    else:
        objekter = data.get('objekter', [])

    liste = []
    for obj in objekter:
        try:
            # Hent koordinater
            wkt = obj['geometri']['wkt']
            coords = wkt.replace("POINT (", "").replace(")", "").split(" ")
            lon, lat = coords[0], coords[1]
            
            type_atk, retning = 1, 0
            # Bruker .get på egenskaper (som er inne i hvert objekt)
            egenskaper = obj.get('egenskaper', [])
            for eg in egenskaper:
                navn = eg.get('navn', '')
                verdi = str(eg.get('verdi', ''))
                if navn == 'Type' and 'Strekning' in verdi:
                    type_atk = 2
                if navn == 'Kontrollerer trafikk i retning':
                    retning = 1 if "Med" in verdi else 2

            liste.append([lat, lon, retning, type_atk])
        except Exception as e:
            continue

    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(liste)
    print(f"Ferdig! Lagret {len(liste)} fotobokser.")

if __name__ == "__main__":
    hent_alle_atk()
