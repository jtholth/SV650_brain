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
    print("Henter data fra Vegvesenet og bygger ATK.csv...")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'ESP32-Project'}
    alle_rader = []
    strekninger = {}

    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
        res = requests.get(url, params=params, headers=headers)
        
        if res.status_code == 200:
            for obj in res.json().get('objekter', []):
                
                # HENTER ID: Her plukker vi ut den unike VEGOBJEKT-IDen!
                atk_id = obj.get('id', 'Ukjent')
                
                coords = re.findall(r"[-+]?\d*\.?\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = float(coords[0]), float(coords[1])
                
                fart = 80
                retning = "MED"
                ref_lat, ref_lon = lat, lon  # Fallback
                vls_id = None
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    retning = seg.get('retning', 'MED').upper()
                    vls_id = seg.get('veglenkesekvensid')
                    
                    if vls_id:
                        # 1. Hent geometri for hele veistrekket (Oppdatert URL)
                        v_url = f"https://nvdbapiles.atlas.vegvesen.no/vegnett/veglenkesekvenser/{vls_id}"
                        v_res = requests.get(v_url, headers=headers)
                        if v_res.status_code == 200:
                            data = v_res.json()
                            ref_wkt = data.get('geometri', {}).get('wkt', '')
                            r_coords = re.findall(r"[-+]?\d*\.?\d+", ref_wkt)
                            
                            if len(r_coords) >= 2:
                                test_lon, test_lat = float(r_coords[0]), float(r_coords[1])
                                
                                # SMART-SJEKK: Hvis startpunktet er under 10m fra boksen, bruk sluttpunktet
                                if len(r_coords) >= 4 and haversine(lat, lon, test_lat, test_lon) < 10:
                                    test_lon, test_lat = float(r_coords[-2]), float(r_coords[-1])
                                    
                                ref_lon, ref_lat = test_lon, test_lat

                        # 2. Hent nøyaktig fart (Tabell 105)
                        f_url = "https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105"
                        f_res = requests.get(f_url, params={'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}, headers=headers)
                        if f_res.status_code == 200 and f_res.json().get('objekter'):
                            for e in f_res.json()['objekter'][0].get('egenskaper', []):
                                if e.get('id') == 2021:
                                    fart = int(e.get('verdi', 80))
                                    break
                
                if obj_type == "103":
                    variabel_avstand = int((fart / 3.6) * 30) 
                    # MATCH ESP32: [ID, Lon, Lat, refLon, refLat, fart, retning, avstand]
                    alle_rader.append([atk_id, lon, lat, ref_lon, ref_lat, fart, retning, variabel_avstand])
                else:
                    if vls_id not in strekninger: strekninger[vls_id] = []
                    strekninger[vls_id].append({
                        'id': atk_id, 'lat': lat, 'lon': lon, 'ref_lat': ref_lat, 'ref_lon': ref_lon, 
                        'fart': fart, 'retning': retning
                    })

    for vls_id, punkter in strekninger.items():
        if len(punkter) >= 2:
            dist = int(haversine(punkter[0]['lat'], punkter[0]['lon'], punkter[1]['lat'], punkter[1]['lon']))
            for p in punkter[:2]:
                # MATCH ESP32: [ID, Lon, Lat, refLon, refLat, fart, retning, avstand]
                alle_rader.append([p['id'], p['lon'], p['lat'], p['ref_lon'], p['ref_lat'], p['fart'], p['retning'], dist])

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    print("Ferdig. Filen 'ATK.csv' er klar.")

if __name__ == "__main__":
    hent_fotobokser()
