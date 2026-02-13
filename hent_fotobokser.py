import requests
import csv

def hent_alle_atk():
    # Bruker det offisielle v4 endepunktet
    base_url = "https://nvdbapiles-v4.atlas.vegvesen.no/vegobjekter/162"
    
    headers = {
        "Accept": "application/json",
        "X-Client": "SV650-Brain-Project"
    }
    
    params = {
        'inkluder': 'egenskaper,geometri',
        'srid': '4326',
        'alle_versjoner': 'false'
    }
    
    liste = []
    current_url = base_url
    
    print("Henter data fra NVDB API v4...")
    
    # Vi kjører en loop for å håndtere alle sidene med data
    while current_url:
        response = requests.get(current_url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Feil fra API: {response.status_code}")
            break
            
        data = response.json()
        objekter = data.get('objekter', [])
        
        for obj in objekter:
            try:
                # Hent koordinater (v4 har ofte punkt-geometri her)
                wkt = obj.get('geometri', {}).get('wkt', '')
                if 'POINT' in wkt:
                    coords = wkt.replace('POINT (', '').replace(')', '').split()
                    lon, lat = coords[0], coords[1]
                    
                    type_atk = 1 # 1 = Punkt-ATK
                    retning = 0  # 0 = Begge/Ukjent
                    
                    # Finn egenskaper i v4-strukturen
                    for eg in obj.get('egenskaper', []):
                        navn = eg.get('navn', '')
                        verdi = str(eg.get('verdi', ''))
                        
                        if 'Type' in navn and 'Strekning' in verdi:
                            type_atk = 2 # 2 = Streknings-ATK
                        
                        if 'retning' in navn.lower():
                            if 'Med' in verdi: retning = 1
                            elif 'Mot' in verdi: retning = 2
                    
                    liste.append([lat, lon, retning, type_atk])
            except Exception:
                continue
        
        # Sjekk om det finnes en neste side (paginering)
        metadata = data.get('metadata', {})
        neste = metadata.get('neste', {})
        current_url = neste.get('href') # API v4 gir full URL til neste side her
        params = None # Parametere ligger allerede i 'neste' URL-en
        
        print(f"Fant {len(liste)} fotobokser så langt...")

    # Lagre til fil (commit og push håndteres av GitHub Actions)
    with open('ATK.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        if liste:
            writer.writerows(liste)
            print(f"Suksess! Lagret totalt {len(liste)} fotobokser til ATK.csv")
        else:
            print("Ingen data funnet. Sjekk API-tilgang.")

if __name__ == "__main__":
    hent_alle_atk()
