import csv
import math

def last_ned_atk_data(filnavn):
    fotobokser = []
    with open(filnavn, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for rad in reader:
            fotobokser.append({
                'type': rad[0],
                'lat': float(rad[1]),
                'lon': float(rad[2]),
                'fart': rad[3],
                'retning': rad[4],
                'meter': int(rad[5])
            })
    return fotobokser

def beregn_logikk(bil_meter_n_minus_1, bil_meter_nå, boks):
    # 1. Finn din kjøreretning
    din_retning = "MED" if bil_meter_nå > bil_meter_n_minus_1 else "MOT"
    
    # 2. Er du på vei mot boksen?
    avstand_nå = abs(boks['meter'] - bil_meter_nå)
    avstand_før = abs(boks['meter'] - bil_meter_n_minus_1)
    paa_vei_mot = avstand_nå < avstand_før
    
    # 3. Den gyldne logikken din:
    # Vi skal varsle hvis (Du kjører MED og boks ser MOT) eller (Du kjører MOT og boks ser MED)
    skal_varsle = False
    if paa_vei_mot:
        if (din_retning == "MED" and boks['retning'] == "MOT") or \
           (din_retning == "MOT" and boks['retning'] == "MED"):
            skal_varsle = True
            
    return skal_varsle, avstand_nå

# --- SIMULERING ---
bokser = last_ned_atk_data('ATK.csv')

# Tenk deg at du kjører på E18. 
# Forrige sekund var du på meter 500. Nå er du på meter 550 (Du kjører MED).
forrige_meter = 500
naavaerende_meter = 550

print(f"Kjøreretning detektert: {'MED' if naavaerende_meter > forrige_meter else 'MOT'}")
print("-" * 50)

for boks in bokser:
    varsel, avstand = beregn_logikk(forrige_meter, naavaerende_meter, boks)
    
    # Vi varsler bare hvis boksen er nærmere enn 1000 meter og logikken stemmer
    if varsel and avstand < 1000:
        type_navn = "Fast ATK" if boks['type'] == '1' else "Strekning"
        print(f"!!! VARSEL: {type_navn} om {int(avstand)} meter!")
        print(f"    Grense: {boks['fart']} km/t | Kameraet ser: {boks['retning']}")
