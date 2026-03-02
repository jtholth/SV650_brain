import requests
import csv
import re
from math import radians, cos, sin, asin, sqrt

# Haversine-formel for å regne meter fra koordinater
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000 # Jordens radius i meter
    return c * r

def hent_norske_fotobokser():
    print("Beregner avstander for streknings-ATK manuelt...")
    headers = {'Accept': 'application/vnd.vegvesen.nvdb-v4+json', 'X-Client': 'SV650-Project'}
    
    alle_rader = []
    strekninger = {} # For å pare kameraer i strekningsmålinger

    for obj_type in ["103", "823"]:
        url = f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/{obj_type}"
        params = {'inkluder': 'geometri,vegsegmenter', 'srid': '4326'}
        res = requests.get(url, params=params, headers=headers)
        
        if res.status_code == 200:
            for obj in res.json().get('objekter', []):
                coords = re.findall(r"[-+]?\d*\.?\d+", obj['geometri']['wkt'])
                if not coords: continue
                lon, lat = coords[0], coords[1]
                
                fart = "80"
                retning = "MED"
                vls_id = None
                
                if 'vegsegmenter' in obj and len(obj['vegsegmenter']) > 0:
                    seg = obj['vegsegmenter'][0]
                    retning = seg.get('retning', 'MED').upper()
                    vls_id = seg.get('veglenkesekvensid')
                    
                    # Hent fartsgrense (din metode)
                    if vls_id:
                        f_res = requests.get(f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/105", 
                                             params={'veglenkesekvens': vls_id, 'inkluder': 'egenskaper'}, headers=headers)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            if f_data.get('objekter'):
                                for e in f_data['objekter'][0].get('egenskaper', []):
                                    if e.get('id') == 2021:
                                        fart = str(e.get('verdi'))
                                        break
                
                if obj_type == "103":
                    meter = obj['vegsegmenter'][0].get('vegsystemreferanse', {}).get('meter', 0)
                    alle_rader.append([1, lat, lon, fart, retning, int(meter)])
                else:
                    # For strekning (823): Lagre for å beregne avstand senere
                    if vls_id not in strekninger:
                        strekninger[vls_id] = []
                    strekninger[vls_id].append({'lat': lat, 'lon': lon, 'fart': fart, 'retning': retning})

    # NÅ REGNER VI UT AVSTANDEN FOR STREKNINGER (823)
    for vls_id, punkter in strekninger.items():
        if len(punkter) >= 2:
            # Vi regner avstand fra punkt 1 til punkt 2
            p1, p2 = punkter[0], punkter[1]
            avstand = haversine(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
            
            # Legg til begge punktene i fila, men nå med beregnet avstand mellom dem
            alle_rader.append([2, p1['lat'], p1['lon'], p1['fart'], p1['retning'], int(avstand)])
            alle_rader.append([2, p2['lat'], p2['lon'], p2['fart'], p2['retning'], int(avstand)])

    with open('ATK.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(alle_rader)
    print(f"Ferdig! Beregnet {len(strekninger)} strekningsmålinger.")

if __name__ == "__main__":
    hent_norske_fotobokser()
