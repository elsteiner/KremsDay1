"""
Brutto-Netto Rechner (Österreich) mit ein-/ausschaltbaren Beitragsarten.

Design:
- Konfigurierbare Beitragsarten (Toggles) und Prozentsätze.
- Unterstützt Brutto -> Netto (auf Arbeitnehmerseite) und Netto -> Brutto (numerisch).
- Einkommensteuer als progressive Stufentabelle (konfigurierbar).
- Ausgabe: detaillierte Aufschlüsselung der Abzüge.

Hinweis:
- Dieses Skript rechnet auf Arbeitnehmer-Seite (Arbeitnehmeranteile).
- Trage die korrekten Prozentsätze / Stufen entsprechend der aktuellen Rechtslage ein.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import math

@dataclass
class ContributionConfig:
    include_pension: bool = True               # Pensionsversicherung (PV)
    include_unemployment: bool = True          # Arbeitslosenversicherung (ALV)
    include_health: bool = True                # Krankenversicherung (KV)
    include_ak_umlage: bool = True             # AK-Umlage
    include_wohnbaubeitrag: bool = True        # Wohnbauförderung (z.B. pauschal / %-Satz)
    # Prozentsätze als Dezimal (z.B. 0.18 = 18%)
    pension_rate: float = 0.1025               # Beispiel: 10.30% Arbeitnehmeranteil
    pension_fixed: float = 0
    unemployment_rate: float = 0.00295          # Beispiel: 0.30%
    health_rate: float = 0.0387                # Beispiel: 3.50%
    ak_umlage_rate: float = 0.0050             # Beispiel: 0.50%
    wohnbau_rate: float = 0.0050               # Beispiel: 0.15%
    # optional: fixer prozentualer oder fixer Euro-betrag für wohnbau
    wohnbau_fixed: float = 0.0                 # Falls Wohnbauförderung als fixer Betrag
    # Sozialversicherung wird auf Bruttogehalt angewandt (vereinfachte Annahme)

@dataclass
class TaxConfig:
    # progressive brackets as list of (upper_threshold, marginal_rate)
    # thresholds in EUR. The last bracket can use math.inf for no upper cap.
    # Example format: [(11000, 0.0), (18000, 0.20), (31000, 0.35), (60000, 0.42), (90000, 0.48), (math.inf, 0.50)]
    brackets: List[Tuple[float, float]] = field(default_factory=lambda: [
        (11000, 0.0),
        (18000, 0.20),
        (31000, 0.35),
        (60000, 0.42),
        (90000, 0.48),
        (math.inf, 0.50),
    ])
    # ggf. Absetzbeträge oder Sonderregelungen können als fixer Betrag eingetragen
    tax_credits: float = 0.0  # direkte Absetzbeträge (z.B. Verkehrs- oder Sozialabsetzbetrag)
    # Hinweis: österreichische Absetzbeträge sollten separat berücksichtigt

def compute_social_contributions(gross: float, conf: ContributionConfig) -> Dict[str, float]:
    """Berechnet die Arbeitnehmer-Sozialabgaben (nur Beispiele/vereinfachte Annahme)."""
    detail = {}
    base = gross
    # Schritt-für-Schritt Berechnung (direkte Formeln)
    if conf.include_pension:
        if conf.pension_fixed > 0:
            pv = round(conf.pension_fixed, 2)
        else:
            pv = round(base * conf.pension_rate, 2)
    else:
        pv = 0.0
    detail['pension'] = pv

    if conf.include_unemployment:
        alv = round(base * conf.unemployment_rate, 2)
    else:
        alv = 0.0
    detail['unemployment'] = alv

    if conf.include_health:
        kv = round(base * conf.health_rate, 2)
    else:
        kv = 0.0
    detail['health'] = kv

    if conf.include_ak_umlage:
        ak = round(base * conf.ak_umlage_rate, 2)
    else:
        ak = 0.0
    detail['ak_umlage'] = ak

    if conf.include_wohnbaubeitrag:
        if conf.wohnbau_fixed > 0:
            wohn = round(conf.wohnbau_fixed, 2)
        else:
            wohn = round(base * conf.wohnbau_rate, 2)
    else:
        wohn = 0.0
    detail['wohnbau'] = wohn

    detail['total_social'] = round(pv + alv + kv + ak + wohn, 2)
    return detail

def compute_income_tax(taxable_income: float, tax_conf: TaxConfig) -> float:
    """
    Berechnet die Einkommensteuer progressiv anhand tax_conf.brackets.
    Brackets: Liste (upper_threshold, marginal_rate). Berechnet Schraubenweise.
    """
    tax = 0.0
    lower = 0.0
    for upper, rate in tax_conf.brackets:
        if taxable_income <= lower:
            break
        segment_upper = min(upper/12, taxable_income)
        taxable_segment = max(0.0, segment_upper - lower)
        # Steuer für dieses Segment
        seg_tax = taxable_segment * rate
        tax += seg_tax
        # move to next bracket
        lower = upper/12
        if segment_upper >= taxable_income:
            break
    # Abzüge / Absetzbeträge
    tax = max(0.0, tax - tax_conf.tax_credits)
    return round(tax, 2)

def brutto_to_net(gross: float, conf: ContributionConfig, tax_conf: TaxConfig) -> Dict[str, float]:
    """
    Hauptfunktion: berechnet Nettoeinkommen aus Brutto (Arbeitnehmeranteile).
    return: dict mit aufgeschlüsselten Positionen.
    """
    # 1) Sozialbeiträge
    social = compute_social_contributions(gross, conf)
    total_social = social['total_social']

    # 2) Steuerpflichtiges Einkommen
    # Achtung: in echten Fällen können bestimmte SV-Abzüge das steuerpflichtige Einkommen mindern.
    # Hier vereinfachte Annahme: steuerpflichtiges Einkommen = brutto - (Arbeitnehmer-SV)
    taxable_income = max(0.0, gross - total_social)

    # 3) Einkommensteuer (progressiv)
    income_tax = compute_income_tax(taxable_income, tax_conf)

    # 4) Netto
    net = round(gross - total_social - income_tax, 2)

    # Ergebnis-Dict
    res = {
        'gross': round(gross, 2),
        'social_breakdown': social,
        'taxable_income': round(taxable_income, 2),
        'income_tax': income_tax,
        'net': net
    }
    return res

def net_to_brutto(target_net: float, conf: ContributionConfig, tax_conf: TaxConfig, guess: float = None) -> Dict[str, float]:
    """
    Näherung: Sucht per Binär- bzw. Intervallsuche ein Brutto, das zu target_net führt.
    Liefert die gleiche Struktur wie brutto_to_net plus Differenzinformation.
    """
    # Suchebereich: [low, high]. low = target_net (mindestens), high = target_net * 5 (konservativ)
    low = max(0.0, target_net)
    high = max(target_net * 1.5 + 1000, target_net + 4000)  # initialer hoher Wert
    # Falls guess gegeben, benutze als Startbereich um guess:
    if guess:
        low = max(0.0, guess * 0.5)
        high = guess * 1.5 + 1000

    # Binäre Suche mit Toleranz
    for _ in range(60):
        mid = (low + high) / 2.0
        computed = brutto_to_net(mid, conf, tax_conf)
        net_mid = computed['net']
        # Schrittweise Vergleich
        if abs(net_mid - target_net) <= 0.01:
            result = computed.copy()
            result['guessed_brutto'] = round(mid, 2)
            result['net_diff'] = round(net_mid - target_net, 2)
            return result
        if net_mid > target_net:
            # Wir haben zu viel Netto → Brutto kann kleiner sein
            high = mid
        else:
            low = mid
    # Falls nicht genau gefunden, gib nächste Annäherung zurück
    mid = (low + high) / 2.0
    result = brutto_to_net(mid, conf, tax_conf)
    result['guessed_brutto'] = round(mid, 2)
    result['net_diff'] = round(result['net'] - target_net, 2)
    return result

# --------- Beispielnutzung ----------
if __name__ == "__main__":
    # Beispiel-Konfiguration für "RAA", wie du es beschrieben hast:
    # - keine PV? (Du hattest gesagt: für RAA keine PV und keine Arbeitslosenversicherung sowie AK-Umlage)
    # Ich interpretiere das so: diese Beiträge werden bei RAA nicht vom Arbeitnehmer abgeführt.
    # Krankenversicherung und Wohnbauförderung sollen beibehalten werden.
    conf_raa = ContributionConfig(
        include_pension=True,
        include_unemployment=False,
        include_ak_umlage=False,
        include_health=True,
        include_wohnbaubeitrag=True,
        # Beispielraten – unbedingt anpassen:
        health_rate=0.0387,
        wohnbau_rate=0.005,
        pension_fixed=297.25,
        #pension_fixed = 415,
        unemployment_rate = 0.0295,
        pension_rate = 0.1025,
        wohnbau_fixed=0.0
    )
    conf_uni = ContributionConfig(
        include_pension=True,
        include_unemployment=True,
        include_ak_umlage=True,
        include_health=True,
        include_wohnbaubeitrag=True,
        # Beispielraten – unbedingt anpassen:
        health_rate=0.0387,
        wohnbau_rate=0.005,
        unemployment_rate = 0.0295,
        pension_rate = 0.1025,
    )

    # Beispiel-Steuertabelle (platzhalter): unbedingt mit aktuellen Sätzen ersetzen
    tax_conf_example = TaxConfig(
        brackets=[
            (13308, 0.0),
            (21617, 0.20),
            (35836, 0.30),
            (69166, 0.40),
            (103072, 0.48),
            (math.inf, 0.50),
        ],
        tax_credits=40.58
    )

    # Test: Brutto 4.500 EUR
    brutto = 4500.0
    result = brutto_to_net(brutto, conf_raa, tax_conf_example)
    print("Brutto->Netto Beispiel (RAA-Konfig):")
    print(result)
    print("\n")
    # Test2: Brutto: 762 EUR, 940.98
    brutto = 940.98
    result2 = brutto_to_net(brutto, conf_uni, tax_conf_example)
    print("Brutto->Netto Beispiel (UNI-Konfig):")
    print(result2)
    print("\n")
    print(result["net"] + result2["net"])
    

    # Test: Netto → Brutto (z.B. du willst 2.300 Netto)
    #target_net = 2300.0
    #rev = net_to_brutto(target_net, conf_raa, tax_conf_example)
    #print("\nNetto->Brutto Annäherung (RAA-Konfig):")
    #print(rev)
