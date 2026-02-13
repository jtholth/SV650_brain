import requests
import csv

def hent_alle_atk():
    # Objekt 162 er fotobokser (både punkt og strekning)
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    liste = []

    for obj in data.get('objekter', []):
        try:
            # Posisjon
            lon = obj['geometri']['wkt'].split('(')[1].split(' ')[0]
            lat = obj['geometri']['wkt'].split(' ')[1].split(')')[0]
            
            # Finn ut om det er punkt eller del av strekning
            type_atk = 1 # Standard Punkt-ATK
            retning = 0
            
            for eg in obj['egenskaper']:
                if eg['navn'] == 'Type':
                    if 'Strekning' in eg['verdi']:
                        type_atk = 2 # Vi merker den som strekning
                if eg['navn'] == 'Kontrollerer trafikk i retning':
                    retning = 1 if eg['verdi'] == "Med metrering" else 2

            liste.append([lat, lon, retning, type_atk])
        except:
            continue

    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(liste)

if __name__ == "__main__":
    hent_alle_atk()
