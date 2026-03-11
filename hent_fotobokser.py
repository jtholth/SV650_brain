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
    try:
        if not wkt_str or '(' not in wkt_str:
            return None, None
        content = wkt_str[wkt_str.find('(')+1 : wkt_str.rfind(')')]
        points = content.split(',')
        target_point = points[index].strip().split()
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
        print(f"Laster ned {len(objekter)} fotobokser. Dette kan ta noen sekunder...\n")
        
        for obj in objekter:
            atk_id = obj.get('id', 'Ukjent')
            wkt_boks = obj.get('geometri', {}).get('wkt', '')
            
            lon, lat = parse_wkt_point(wkt_boks, 0)
            if lon is None or lat is None: 
                continue
                
            fart = 80 # Standardverdi hvis API-et feiler
            retning = "MED"
            ref_lat, ref_lon = lat, lon  # Nødløsning
            
            if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                seg = obj['vegsegmenter'][0]
                retning = seg.get('retning', 'MED').upper()
                vls_id = seg.get('veglenkesekvensid')
                rel_pos = seg.get('relativPosisjon') 
                
                if vls_id:
                    v_url = f"https://nvdbapiles.atlas.vegvesen.no/vegnett/veglenkesekvenser/{vls_id}?srid=4326"
                    v_res = requests.get(v_url, headers=headers)
                    
                    if v_res.status_code == 200:
                        v_data = v_res.json()
                        ref_wkt = ""
                        last_wkt = ""
                        
                        if 'veglenker' in v_data and len(v_data['veglenker']) > 0:
                            veglenker = sorted(v_data['veglenker'], key=lambda x: x.get('startposisjon', 0))
                            ref_wkt = veglenker[0].get('geometri', {}).get('wkt', '')
                            last_wkt = veglenker[-1].get('geometri', {}).get('wkt', '')
                        elif 'geometri' in v_data:
                            ref_wkt = v_data.get('geometri', {}).get('wkt', '')
                            last_wkt = ref_wkt
                        
                        test_lon, test_lat = parse_wkt_point(ref_wkt, 0)
                        
                        if test_lon is not None and test_lat is not None:
                            if haversine(lat, lon, test_lat, test_lon) < 10:
                                t_lon, t_lat = parse_wkt_point(last_wkt, -1)
                                if t_lon is not None:
                                    test_lon, test_lat = t_lon, t_lat
                                    
                            ref_lon, ref_lat = test_lon, test_lat
                    
                    # --- RETTET OPP I API-SPØRRINGEN HER ---
                    if rel_pos is not None:
                        f_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        # NVDB krever formatet: relativPosisjon@veglenkesekvensid (f.eks 0.45@123456)
                        f_params = {'veglenkesekvens': f"{rel_pos}@{vls_id}", 'inkluder': 'egenskaper'}
                        f_res = requests.get(f_url, params=f_params, headers=headers)
                        
                        if f_res.status_code == 200 and f_res.json().get('objekter'):
                            for e in f_res.json()['objekter'][0].get('egenskaper', []):
                                if e.get('id') == 2021: # 2021 er egenskapen "Fartsgrense"
                                    fart = int(e.get('verdi', 80))
                                    break
            
            variabel_avstand = int((fart / 3.6) * 10) 
            print(f"Boks {atk_id}: Fartsgrense funnet = {fart} km/t")
            
            alle_rader.append([atk_id, lat, lon, ref_lat, ref_lon, fart, retning, variabel_avstand])

        with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(alle_rader)
            
        print(f"\nSuksess! Lagret {len(alle_rader)} ekte fotobokser i 'ATK.csv'.")
    else:
        print(f"Feil mot NVDB. Status: {res.status_code}")

if __name__ == "__main__":
    hent_fotobokser()
