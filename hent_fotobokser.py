import requests
import csv

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB)...")
    
    # 103 = Punkt-ATK, 823 = Streknings-ATK
    url = "https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/103,823"
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326'
    }
    
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v3-rev1+json',
        'X-Client': 'SV650-Brain-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Lagrer til filnavnet du valgte: ATK.csv
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            antall = 0
            for obj in data.get('objekter', []):
                # Type 1 = Fast boks, Type 2 = Strekning
                obj_type = 1 if obj['metadata']['type']['id'] == 103 else 2
                
                # Hent koordinater
                try:
                    wkt = obj['geometri']['wkt']
                    coords = wkt.replace('POINT (', '').replace(')', '').split(' ')
                    lon = coords[0]
                    lat = coords[1]
                except (KeyError, IndexError):
                    continue
                
                # Finn fartsgrense
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
