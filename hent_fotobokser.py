import requests
import csv

def hent_alle_atk():
    # NVDB API URL for objekt 162 (Fotoboks)
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    
    # Viktig: API-et krever spesifikk versjon i headeren for stabil respons
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain-Project"
    }
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326'
    }
    
    print("Kobler til NVDB...")
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Kunne ikke hente data: {e}")
        return

    # NVDB V3 pakker objektene inn i 'objekter' nøkkelen
    objekter = data.get('objekter', [])
    
    liste = []
    print(f"Fant {len(objekter)} objekter. Prosesserer...")

    for obj in objekter:
        try:
            # Hent koordinater
            geometri = obj.get('geometri', {})
            wkt = geometri.get('wkt', '')
            if not wkt: continue
            
            # Ekstraher lat/lon fra POINT (LON LAT)
            coords = wkt.split('(')[1].split(')')[0].split(' ')
            lon = coords[0]
            lat = coords[1]
            
            type_atk = 1 
            retning = 0
            
            egenskaper = obj.get('egenskaper', [])
            for eg in egenskaper:
                if eg['navn'] == 'Type':
                    if 'Strekning' in str(eg['verdi']):
                        type_atk = 2
                if eg['navn'] == 'Kontrollerer trafikk i retning':
                    if "Med" in str(eg['verdi']):
                        retning = 1
                    elif "Mot" in str(eg['verdi']):
                        retning = 2

            liste.append([lat, lon, retning, type_atk])
        except:
            continue

    if liste:
        with open('ATK.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(liste)
        print(f"Suksess! Lagret {len(liste)} fotobokser til ATK.csv")
    else:
        print("Ingen data ble lagret. Sjekk API-responsen.")

if __name__ == "__main__":
    hent_alle_atk()
