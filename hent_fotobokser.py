import requests
import csv

def hent_alle_atk():
    # Bruker versjon 3 av API-et
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/162"
    headers = {
        "Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
        "X-Client": "SV650-Brain-Project"
    }
    # Vi henter alle aktive fotobokser i Norge
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    print("Kobler til NVDB API...")
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"Feil fra API: {response.status_code}")
        return

    data = response.json()
    
    # Håndterer både liste og objekt-respons
    objekter = data if isinstance(data, list) else data.get('objekter', [])
    
    print(f"Antall objekter mottatt: {len(objekter)}")

    liste = []
    for obj in objekter:
        try:
            # Hent koordinater fra geometri-feltet
            geometri = obj.get('geometri', {})
            wkt = geometri.get('wkt', '') # Format: "POINT (10.123 59.123)"
            
            if 'POINT' in wkt:
                # Rens teksten så vi bare står igjen med tallene
                coords_str = wkt.split('(')[1].split(')')[0]
                parts = coords_str.split()
                lon = parts[0]
                lat = parts[1]
                
                type_atk = 1 # Punkt
                retning = 0 # Ukjent
                
                # Sjekk egenskaper for type og retning
                for eg in obj.get('egenskaper', []):
                    navn = eg.get('navn', '')
                    verdi = str(eg.get('verdi', ''))
                    
                    if navn == 'Type' and 'Strekning' in verdi:
                        type_atk = 2
                    if navn == 'Kontrollerer trafikk i retning':
                        if 'Med' in verdi: retning = 1
                        elif 'Mot' in verdi: retning = 2

                liste.append([lat, lon, retning, type_atk])
        except Exception as e:
            continue

    # Skriv til fil
    if len(liste) > 0:
        with open('ATK.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(liste)
        print(f"Suksess! Lagret {len(liste)} rader til ATK.csv")
    else:
        print("ADVARSEL: Ingen rader ble generert. Sjekk API-strukturen.")

if __name__ == "__main__":
    hent_alle_atk()
