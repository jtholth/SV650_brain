import requests
import csv

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB)...")
    
    # Vi henter objekt 103 (Punkt-ATK) og 823 (Streknings-ATK)
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/103,823"
    
    # Vi legger til 'vegsystemreferanse' for å gjøre spørringen gyldig
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'vegsystemreferanse': 'E,R,F' # Europavei, Riksvei, Fylkesvei
    }
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v3-rev1+json',
        'X-Client': 'SV650-Brain-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        
        # Hvis det fortsatt feiler, skriver vi ut hva serveren faktisk sier
        if response.status_code != 200:
            print(f"Server svarte med feilkode {response.status_code}: {response.text}")
            response.raise_for_status()

        data = response.json()
        
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            antall = 0
            # NVDB returnerer objektene i en liste kalt 'objekter'
            for obj in data.get('objekter', []):
                obj_type = 1 if obj['metadata']['type']['id'] == 103 else 2
                
                try:
                    wkt = obj['geometri']['wkt']
                    coords = wkt.replace('POINT (', '').replace(')', '').split(' ')
                    lon = coords[0]
                    lat = coords[1]
                except (KeyError, IndexError):
                    continue
                
                fart = 80 
                for egenskap in obj.get('egenskaper', []):
                    if "fartsgrense" in egenskap.get('navn', '').lower():
                        fart = egenskap.get('verdi', 80)
                
                writer.writerow([obj_type, lat, lon, fart])
                antall += 1
                
        print(f"Suksess! Lagret {antall} punkter i 'ATK.csv'.")
        
    except Exception as e:
        print(f"Feil ved henting av data: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
