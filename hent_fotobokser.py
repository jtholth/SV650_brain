import requests
import csv

def hent_alle_atk():
    # Vi bruker /vegobjekter direkte for å få selve innholdet
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain"
    }
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    print("Henter data fra NVDB...")
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    # NVDB pakker objektene inn i en liste som heter 'objekter'
    objekter = data.get('objekter', [])
    print(f"Fant {len(objekter)} fotobokser.")

    liste = []
    for obj in objekter:
        try:
            # Hent WKT (geometri)
            wkt = obj.get('geometri', {}).get('wkt', '')
            if 'POINT' in wkt:
                # Splitt ut koordinater
                p = wkt.replace('POINT (', '').replace(')', '').split()
                lon, lat = p[0], p[1]
                
                type_atk = 1
                retning = 0
                
                # Finn type og retning i egenskapene
                for eg in obj.get('egenskaper', []):
                    if 'Type' in eg['navn']:
                        if 'Strekning' in str(eg['verdi']): type_atk = 2
                    if 'retning' in eg['navn'].lower():
                        if 'Med' in str(eg['verdi']): retning = 1
                        elif 'Mot' in str(eg['verdi']): retning = 2
                
                liste.append([lat, lon, retning, type_atk])
        except:
            continue

    if liste:
        with open('ATK.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(liste)
        print(f"Lagret {len(liste)} rader til ATK.csv")
    else:
        print("Feil: Fant ingen data å lagre.")

if __name__ == "__main__":
    hent_alle_atk()
