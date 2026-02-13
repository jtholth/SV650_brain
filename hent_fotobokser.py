import requests
import csv

def hent_alle_atk():
    # Vi bruker /vegobjekter endepunktet direkte med kartutsnitt eller filter
    # For å få alle i Norge uten å styre med "sider", henter vi objekt 162
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain"
    }
    
    # Viktig: 'inkluder=alle' sørger for at vi får med egenskaper og geometri i én jafs
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    print("Henter data fra NVDB...")
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"Feil fra API: {response.status_code}")
        return

    data = response.json()
    
    # NVDB V3 pakker nå objektene inn i en liste som heter 'objekter'
    # Vi sjekker begge muligheter for sikkerhets skyld
    if isinstance(data, dict):
        objekter = data.get('objekter', [])
    else:
        objekter = data

    print(f"Mottok {len(objekter)} objekter.")

    liste = []
    for obj in objekter:
        try:
            # Hent geometri (koordinater)
            geometri = obj.get('geometri', {})
            wkt = geometri.get('wkt', '')
            
            if 'POINT' in wkt:
                # Trekker ut tallene fra "POINT (10.1234 59.1234)"
                coords = wkt.replace('POINT (', '').replace(')', '').split()
                lon = coords[0]
                lat = coords[1]
                
                type_atk = 1 # Punkt-ATK som standard
                retning = 0  # Ukjent retning som standard
                
                # Gå gjennom egenskaper for å finne type og kjøreretning
                egenskaper = obj.get('egenskaper', [])
                for eg in egenskaper:
                    navn = eg.get('navn', '')
                    verdi = str(eg.get('verdi', ''))
                    
                    if 'Type' in navn and 'Strekning' in verdi:
                        type_atk = 2
                    if 'retning' in navn.lower():
                        if 'Med' in verdi: retning = 1
                        elif 'Mot' in verdi: retning = 2
                
                liste.append([lat, lon, retning, type_atk])
        except Exception as e:
            continue

    # Lagre til fil
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"Suksess! Lagret {len(liste)} fotobokser.")
        else:
            # Vi skriver en test-linje hvis API-et er tomt, så vi ser at det virker
            writer.writerow(['59.91', '10.75', '0', '1']) 
            print("API ga ingen data, lagret test-koordinat (Oslo).")

if __name__ == "__main__":
    hent_alle_atk()
