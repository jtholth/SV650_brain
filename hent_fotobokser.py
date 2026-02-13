import requests
import csv

def hent_alle_atk():
    # Enklest mulig URL for å teste v4
    url = "https://nvdbapiles-v4.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain"
    }
    
    # Vi henter bare de 10 første for å se om vi får kontakt
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'antall': '50' 
    }
    
    print(f"Kontakter: {url}")
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Statuskode: {response.status_code}")
        data = response.json()
    except Exception as e:
        print(f"Kritisk feil ved tilkobling: {e}")
        return

    # Debug: Se hva API-et faktisk inneholder
    objekter = data.get('objekter', [])
    print(f"Antall objekter funnet: {len(objekter)}")

    if len(objekter) == 0:
        print("DEBUG: API-responsen var tom. Her er rådata:")
        print(data) # Dette vil vise oss feilmeldingen fra Vegvesenet i loggen

    liste = []
    for obj in objekter:
        try:
            # Hent koordinater fra v4 struktur
            geometri = obj.get('geometri', {})
            wkt = geometri.get('wkt', '')
            
            if 'POINT' in wkt:
                coords = wkt.replace('POINT (', '').replace(')', '').split()
                lon, lat = coords[0], coords[1]
                
                type_atk = 1
                retning = 0
                
                # Sjekk egenskaper
                for eg in obj.get('egenskaper', []):
                    navn = eg.get('navn', '')
                    verdi = str(eg.get('verdi', ''))
                    if 'Type' in navn and 'Strekning' in verdi: type_atk = 2
                    if 'retning' in navn.lower():
                        if 'Med' in verdi: retning = 1
                        elif 'Mot' in verdi: retning = 2
                
                liste.append([lat, lon, retning, type_atk])
        except Exception as e:
            continue

    # Tving skriving til fil
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"Suksess! Skrev {len(liste)} linjer til ATK.csv")
        else:
            # Hvis listen er tom, skriver vi en feilmelding i fila så den ikke er 0 bytes
            writer.writerow(['FEIL', 'INGEN_DATA_FRA_API', '0', '0'])
            print("Skrev feilmelding til fil (listen var tom).")

if __name__ == "__main__":
    hent_alle_atk()
