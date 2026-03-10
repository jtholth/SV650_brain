import requests
import csv
import math

def haversine(lat1, lon1, lat2, lon2):
    # Beregner fysisk avstand i meter mellom to GPS-koordinater
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def parse_wkt_point(wkt_str, index=0):
    # Henter ut koordinater uansett om det er 2D eller 3D (Z-akse)
    # index 0 for startpunkt, -1 for sluttpunkt
    try:
        content = wkt_str[wkt_str.find('(')+1 : wkt_str.find(')')]
        points = content.split(',')
        target_point = points[index].strip().split()
        # Sender alltid tilbake [Lengdegrad (Lon), Breddegrad (Lat)]
        return float(target_point[0]), float(target_point[1])
    except:
        return None, None

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
            wkt_boks = obj.get('geometri', {}).get('wkt', '')
            
            lon, lat = parse_wkt_point(wkt_boks, 0)
            if lon is None or lat is None: 
                continue
                
            fart = 80
            retning = "MED"
            ref_lat, ref_lon = lat, lon  # Nødløsning
            
            if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                seg = obj['vegsegmenter'][0]
                retning = seg.get('retning', 'MED').upper()
                vls_id = seg.get('veglenkesekvensid')
                
                if vls_id:
                    # FIKSET HER: Fjernet &inkluder=geometri som skapte 400 Bad Request
                    v_url = f"https://nvdbapiles.atlas.vegvesen.no/vegnett/veglenkesekvenser/{vls_id}?srid=4326"
                    v_res = requests.get(v_url, headers=headers)
                    
                    if v_res.status_code == 200:
                        ref_wkt = v_res.json().get('geometri', {}).get('wkt', '')
                        
                        # Robust uthenting av startpunkt som ignorerer Z-koordinater
                        test_lon, test_lat = parse_wkt_point(ref_wkt, 0)
                        
                        if test_lon is not None and test_lat is not None:
                            # SMART-SJEKK: Hvis startpunktet er under 10m fra boksen, bruk sluttpunktet
                            if haversine(lat, lon, test_lat, test_lon) < 10:
                                last_lon, last_lat = parse_wkt_point(ref_wkt, -1)
                                if last_lon is not None:
                                    test_lon, test_lat = last_lon, last_lat
                                    
                            ref_lon, ref_lat = test_lon, test_lat
                    else:
                        print(f"Advarsel: Feil {v_res.status_code} ved henting av veglenke {vls_id}")
                    
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
