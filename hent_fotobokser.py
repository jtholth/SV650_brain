import requests
import csv

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB V3)...")
    
    # Går tilbake til V3 som vi vet fungerer med disse parameterne
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/103,823"
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'vegsystemreferanse': 'E,R,F'
    }
    
    # VIKTIG: Vi bruker en helt nøytral X-Client som ikke blir blokkert
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v3-rev1+json',
        'X-Client': 'NVDB-Python-Client' 
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Server svarte med feilkode {response.status_code}")
            print(f"Melding: {response.text}")
            response.raise_for_status()

        data = response.json()
        
        # Lagrer til din fil: ATK.csv
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            antall = 0
            # NVDB returnerer objektene i en liste kalt 'objekter'
            for obj in data.get('objekter', []):
                # 103 = Fast boks, 823 = Strekningsmåling
                obj_id = obj['metadata']['type']['id']
                obj_type = 1 if obj_id == 103 else 2
                
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
