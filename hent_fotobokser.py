import requests
import csv

def hent_alle_atk():
    # I v4 spesifiserer vi ofte alt i URL-en for å unngå parameter-krøll
    url = "https://nvdbapiles-v4.atlas.vegvesen.no/vegobjekter/162?inkluder=egenskaper,geometri&srid=4326"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain"
    }
    
    print(f"Kontakter: {url}")
    response = requests.get(url, headers=headers)
    print(f"Statuskode: {response.status_code}")

    if response.status_code != 200:
        print("Feil fra API. Her er svaret:")
        print(response.text) # Dette vil vise nøyaktig HVORFOR Vegvesenet avviser oss
        return

    data = response.json()
    objekter = data.get('objekter', [])
    print(f"Antall objekter funnet: {len(objekter)}")

    liste = []
    for obj in objekter:
        try:
            # v4 koordinat-uthenting
            wkt = obj.get('geometri', {}).get('wkt', '')
            if 'POINT' in wkt:
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

    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"Suksess! Lagret {len(liste)} rader.")
        else:
            writer.writerow(['error', 'no_data', '0', '0'])
            print("Listen var tom.")

if __name__ == "__main__":
    hent_alle_atk()
