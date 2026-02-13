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
    
    # FIX: Sjekker om data er en liste direkte eller om det ligger i 'objekter'
    if isinstance(data, list):
        objekter = data
    elif isinstance(data, dict) and 'objekter' in data:
        objekter = data['objekter']
    else:
        print("Uventet format fra API")
        return

    liste = []
    for obj in objekter:
        try:
            wkt = obj['geometri']['wkt']
            coords = wkt.replace("POINT (", "").replace(")", "").split(" ")
            lon, lat = coords[0], coords[1]
            
            type_atk, retning = 1, 0
            for eg in obj.get('egenskaper', []):
                if eg['navn'] == 'Type' and 'Strekning' in str(eg['verdi']):
                    type_atk = 2
                if eg['navn'] == 'Kontrollerer trafikk i retning':
                    retning = 1 if "Med" in str(eg['verdi']) else 2

            liste.append([lat, lon, retning, type_atk])
        except:
            continue

    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(liste)
    print(f"Ferdig! Lagret {len(liste)} rader.")

if __name__ == "__main__":
    hent_alle_atk()
