import requests
import csv
import re
import time

def hent_fart_fra_meter(vegsystemreferanse):
    """
    Tar en referanse som 'FV301 S1D1 m485' og finner fartsgrensen der.
    """
    base_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
    params = {
        'vegsystemreferanse': vegsystemreferanse,
        'inkluder': 'egenskaper',
        'srid': '4326'
    }
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    try:
        # Vi spør: "Hvilket 105-objekt finnes på denne veien på denne meteren?"
        res = requests.get(base_url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for obj in data.get('objekter', []):
                for egenskap in obj.get('egenskaper', []):
                    if egenskap.get('id') == 2021:
                        return str(egenskap.get('verdi', '80'))
    except:
        pass
    return "80"

def hent_norske_fotobokser():
    print("Bruker din meter-logikk: Slår opp boksens plassering i fartsgrense-registeret...")
    
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/103,823"
    params = {'inkluder': 'metadata,vegsegmenter', 'srid': '4326'}
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Feil {response.status_code}")
            return

        objekter = response.json().get('objekter', [])
        alle_rader = []
        
        print(f"Fant {len(objekter)} bokser. Starter nøyaktig farts-oppslag...")

        for i, obj in enumerate(objekter):
            try:
                # 1. Koordinater
                wkt = obj['geometri']['wkt']
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
                lon, lat = coords[0], coords[1]

                # 2. Hent nøyaktig vegsystemreferanse (f.eks. FV301 K S1D1 m485)
                fart = "80"
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    veg_ref = obj['vegsegmenter'][0].get('vegsystemreferanse', {}).get('kortform')
                    if veg_ref:
                        # Nå bruker vi din logikk: Finn farten på denne meteren
                        fart = hent_fart_fra_meter(veg_ref)

                type_id = 1 if obj['metadata']['type']['id'] == 103 else 2
                alle_rader.append([type_id, lat, lon, fart])

                if (i + 1) % 50 == 0:
                    print(f"Behandlet {i + 1} bokser...")
                    
            except:
                continue

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        unike = set([r[3] for r in alle_rader])
        print(f"FERDIG! Lagret {len(alle_rader)} rader. Fant fartsgrenser: {unike}")

    except Exception as e:
        print(f"Krasj: {e}")

if __name__ == "__main__":
    hent_norske_fotobokser()
