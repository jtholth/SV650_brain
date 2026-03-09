import requests
import csv
import re
import math

def haversine(lat1, lon1, lat2, lon2):
    # Beregner fysisk avstand i meter mellom to GPS-koordinater
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def hent_fotobokser():
    print("Henter Punkt-ATK fra tabell 162...")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'ESP32-Project'}
    alle_rader = []
    
    url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/162"
    params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
    
    res = requests.get(url, params=params, headers=headers)
    
    if res.status_code == 200:
        objekter = res.json().get('objekter', [])
        print(f"Laster ned {len(objekter)} fotobokser...")
        
        for obj in objekter:
            atk_id = obj.get('id', 'Ukjent')
            coords = re.findall(r"[-+]?\d*\.?\d+", obj.get('geometri', {}).get('wkt', ''))
            
            if not coords or len(coords) < 2: 
                continue
                
            lon, lat = float(coords[0]), float(coords[1])
            fart = 80
            retning = "MED"
            ref_lat, ref_lon = lat, lon  # Nødløsning hvis startpunkt feiler
            vls_id = None
            
            if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                seg = obj['vegsegmenter'][0]
                retning = seg.get('retning', 'MED').upper()
                vls_id = seg.get('veglenkesekvensid')
                
                if vls_id:
                    # Hent veiens startkoordinater (VIKTIG: srid=4326)
                    v_url = f"https://nvdbapiles.atlas.vegvesen.no/vegnett/veglenkesekvenser/{vls_id}?srid=4326"
                    v_res = requests.get(v_url, headers=headers)
                    
                    if v_res.status_code == 200:
                        ref_wkt = v_res.json().get('geometri', {}).get('wkt', '')
                        r_coords = re.findall(r"[-+]?\d*\.?\d+", ref_wkt)
                        
                        if len(r_coords) >= 2:
                            test_lon, test_lat = float(r_coords[0]), float(r_coords[1])
                            
                            # SMART-SJEKK: Hvis startpunktet er under 10m fra boksen, bruk sluttpunktet
                            if len(r_coords) >= 4 and haversine(lat, lon, test_lat, test_lon) < 10:
                                test_lon, test_lat = float(r_coords[-2]), float(r_coords[-1])
                                
                            ref_lon, ref_lat = test_lon, test_lat
                    
                    # Hent riktig fartsgrense (Tabell 105)
                    f_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                    f_res = requests.get(f_url, params={'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}, headers=headers)
                    if f_res.status_code == 200 and f_res.json().get('objekter'):
                        for e in f_res.json()['objekter'][0].get('egenskaper', []):
                            if e.get('id') == 2021:
                                fart = int(e.get('verdi', 80))
                                break
            
            # ESP32 Forventer format: [ID, Lon, Lat, refLon, refLat, fart, retning, avstand]
            variabel_avstand = int((fart / 3.6) * 30) 
            alle_rader.append([atk_id, lon, lat, ref_lon, ref_lat, fart, retning, variabel_avstand])

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"\nSuksess! Lagret {len(alle_rader)} ekte fotobokser fra tabell 162 i 'ATK.csv'.")
    else:
        print(f"Kunne ikke koble til NVDB. HTTP Status: {res.status_code}")

if __name__ == "__main__":
    hent_fotobokser()
