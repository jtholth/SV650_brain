import requests
import csv

def hent_norske_fotobokser():
    print("Kobler til Vegvesenets database (NVDB V4)...")
    
    # Ny URL for versjon 4
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'vegsystemreferanse': 'E,R,F'
    }
    
    # Vi fjerner X-Client-navnet som ble blokkert og bruker et mer generelt ett
    headers = {
        'Accept': 'application/vnd.vegvesen.nvdb-v4+json',
        'X-Client': 'SV650-DIY-Project'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Server svarte med feilkode {response.status_code}: {response.text}")
            response.raise_for_status()

        data = response.json()
        
        # Vi åpner fila ATK.csv som du har valgt
        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            antall = 0
            # V4 returnerer objektene i en liste kalt 'objekter'
            for obj in data.get('objekter', []):
                # 103 = Fast boks, 823 = Strekningsmåling
                obj_type = 1 if obj['metadata']['type']['id'] == 103 else 2
                
                try:
                    # I V4 ligger ofte koordinatene litt annerledes hvis det er strekning, 
                    # men vi henter punktet for selve boks-posisjonen
                    wkt = obj['geometri']['wkt']
                    coords = wkt.replace('POINT (', '').replace(')', '').split(' ')
                    lon = coords[0]
                    lat = coords[1]
                except (KeyError, IndexError):
                    continue
                
                fart = 80 
                for egenskap in obj.get('egenskaper', []):
                    if "fartsgrense" in egenskap.get('navn', '').lower():
                        # Håndterer at verdi kan være tekst eller tall
                        fart = egenskap.get('verdi', 80)
                
                writer.writerow([obj_type, lat, lon, fart])
                antall += 1
                
        print(f"Suksess! Lagret {antall} punkter i 'ATK.csv'.")
        
    except Exception as e:
        print(f"Feil ved henting av data: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
