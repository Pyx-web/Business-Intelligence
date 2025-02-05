import requests
import logging
import re
from transformers import pipeline
import cohere
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COHERE_API_KEY = ""
co = cohere.Client(COHERE_API_KEY)

GOOGLE_API_KEY = ""
GEONAMES_USER = ""
OPENWEATHER_API_KEY = ""

def show_progress(message):
    logger.info(message)
    time.sleep(1)

def clean_text(text):
    """ Entfernt ungewünschte Zeichen wie #, -, * und formatiert den Text schöner """
    cleaned_text = re.sub(r'[#]', '', text)  # Entfernt -, # und *
    cleaned_text = re.sub(r'[-]', '', text)  # Entfernt -, # und *
    cleaned_text = re.sub(r'[*]', '', text)  # Entfernt -, # und *
    cleaned_text = re.sub(r'[**]', '', text)  # Entfernt -, # und *
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Reduziert mehrere Leerzeichen
    return cleaned_text

# Relevante Branchen-Keywords
KEYWORD_CATEGORIES = [
    "metallbau", "metallverarbeitung", "bauunternehmen", "konstruktion", "handwerksbetrieb", "tiefbau", "hochbau", "anlagenbau", "schweißtechnik", "produktion", "fertigung",
    "landwirtschaft", "bäckerei", "konditorei", "fleischerei", "gastronomie", "hotel", "restauration", "catering", "kfz-werkstatt", "autohandel", "fahrschule", "fischerei", "gartenbau",
    "immobilien", "versicherungen", "finanzdienstleistungen", "büroservice", "reinigungsservice", "logistik", "spedition", "lagerhaltung", "postdienstleistungen", "kurierdienst",
    "krankenhaus", "pflegeheim", "physiotherapie", "arztpraxis", "apotheke", "tierarzt", "zahnarzt", "psychotherapie", "orthopädie", "hno-arzt", "augenarzt", "radiologie",
    "rechtsanwalt", "notar", "steuerberater", "unternehmensberatung", "it-dienstleistungen", "softwareentwicklung", "hardwarehandel", "webdesign", "netzwerkadministration", "cloud-dienstleistungen",
    "grafikdesign", "fotografie", "werbeagentur", "druckerei", "medienproduktion", "videoagentur", "textilherstellung", "modedesign", "schneiderei", "lederwarenherstellung", "schuhherstellung",
    "elektroinstallation", "elektrohandel", "solarenergie", "windenergie", "wasserkraft", "energieberatung", "heizungsbau", "sanitärtechnik", "klimatechnik", "lüftungstechnik",
    "bauingenieur", "architekt", "statiker", "vermessungsbüro", "geotechnik", "holzbau", "betonbau", "stahlschutzbau", "dämmtechnik", "abbruchunternehmen",
    "biotechnologie", "chemische industrie", "lebensmittelproduktion", "pharmaindustrie", "automobilindustrie", "maschinenbau", "robotik", "kunststoffverarbeitung", "metallverarbeitung",
    "it-sicherheit", "datenschutz", "cybersicherheit", "telekommunikation", "rechenzentrum", "hosting", "netzwerkinfrastruktur", "sensorik", "robotik",
    "events", "veranstaltungsorganisation", "messen", "konferenzen", "eventtechnik", "bühnenbau", "lichttechnik", "musikproduktion", "künstlervermittlung", "catering",
    "spielwarenhandel", "buchhandel", "zeitschriftenhandel", "elektronikhandel", "möbelhandel", "baumarkt", "modehandel", "schuhhandel", "sportartikel",
    "jagd", "fischerei", "waldwirtschaft", "agrarhandel", "landmaschinenhandel", "saatgut", "düngemittel", "agrartechnik", "forstwirtschaft", "weinbau",
    "fliesenleger", "malerbetrieb", "tischlerei", "schlosser", "glaserei", "dachdecker", "bauhelfer", "mauerer", "garten- und landschaftsbau", "landschaftsarchitektur",
    "mechaniker", "mechatroniker", "installateur", "kraftfahrzeugmechatroniker", "fahrzeuglackierer", "landmaschinenmechaniker", "heizungsinstallateur", "kfz-techniker",
    "umweltschutz", "abfallwirtschaft", "recycling", "wasserversorgung", "luftreinhaltung", "bodenanalytik", "emissionsmessungen", "klimaforschung", "ressourcenschonung",
    "kindergarten", "schule", "hochschule", "universität", "bildungsträger", "weiterbildung", "berufsausbildung", "sprachschule", "musikschule", "malkurs",
    "pflegepersonal", "altersheim", "krankenpflege", "ambulante pflege", "palliativpflege", "intensivpflege", "therapie", "rehabilitation", "kinderpflege",
    "sicherheitsdienst", "bewachungsdienst", "objektschutz", "brandschutz", "personenschutz", "alarmtechnik", "überwachungstechnik", "gefahrenerkennung",
    "maschinenbau", "robotik", "automatisierungstechnik", "mechatronik", "antriebstechnik", "konstruktionstechnik", "fertigungstechnik", "anlagenbau",
    "speziallogistik", "kühltransporte", "gefahrguttransporte", "seehafenlogistik", "flughafenlogistik", "containertransporte", "gleislogistik",
    "sanitär", "heizung", "elektro", "bau", "energieversorgung", "reparaturservice", "montageservice", "umweltingenieur", "wetterdienst",
    "zimmerei", "fliesenleger", "gerüstbau", "installateur", "spengler", "brandschutztechnik", "fahrzeugtechnik", "haushaltsgeräte-reparatur",
    "betreuungseinrichtungen", "hort", "ferienbetreuung", "jugendzentrum", "sozialeinrichtung", "bildungsberatung", "lehrerfortbildung",
    "medizintechnik", "laborgeräte", "diagnosetechnik", "orthopädietechnik", "zahnmedizinische geräte", "kardiotechnik", "chirurgische geräte",
    "fischverarbeitung", "milchverarbeitung", "getränkeherstellung", "backwarenherstellung", "schokoladenherstellung", "brauereien", "weinkeltereien",
    "kosmetikherstellung", "reinigungsmittelherstellung", "kunststoffproduktion", "papierherstellung", "textilfabriken", "glasproduktion",
    "tourismus", "freizeitparks", "erlebnisbäder", "museen", "sehenswürdigkeiten", "reiseführer", "reisedienstleistungen", "reisefotografie",
    "softwarearchitektur", "datenbanken", "big data", "künstliche intelligenz", "maschinelles lernen", "webentwicklung", "app-entwicklung",
    "windkraftanlagen", "wasserkraftwerke", "geothermie", "biomasse", "energienetze", "batterietechnik", "energiespeicher",
    "drohnenentwicklung", "robotersoftware", "sensortechnik", "automatisierte fahrzeuge", "prozesssteuerung", "ki-infrastruktur",
    "biowissenschaften", "gentechnik", "pflanzenschutz", "forensik", "agrarwissenschaften", "tierschutzwissenschaften",
    "finanztechnologie", "blockchain", "finanzsoftware", "digitalbanking", "investmenttechnologie", "versicherungssoftware",
    "logistiksoftware", "lagerautomatisierung", "robotergestützte logistik", "drohnentransporte", "versandverfolgung",
    "veranstaltungstechnik", "audiotechnik", "lichtgestaltung", "bühnenbild", "messebauten", "innenarchitektur", "museumsbau",
    "outdoor-werbung", "digital signage", "plakatwerbung", "verkehrsplanung", "stadtentwicklung", "denkmalpflege", "landschaftsplanung",
    "textilhandel", "lederwarenhandel", "jeanshandel", "second-hand-bekleidung", "brautmoden", "designermode", "berufsbekleidung",
    "schmuckdesign", "goldschmiede", "uhrmacher", "juwelier", "diamantenhandel", "edelsteinschleiferei", "schmuckrestaurierung",
    "handtaschen", "brillenhandel", "sonnenbrillen", "optiker", "sehhilfen", "kontaktlinsen", "augenoptiktechnik",
    "kindermode", "spielzeugproduktion", "kindermöbel", "krippenausstattung", "schulbedarf", "kinderbücher", "kinderwagen",
    "haushaltsgeräte", "küchengeräte", "waschmaschinen", "kühlschränke", "geschirrspüler", "kaffeemaschinen", "staubsauger",
    "gartengeräte", "rasenmäher", "heckenscheren", "pflanzzubehör", "gartenmöbel", "bewässerungssysteme", "gartenbeleuchtung",
    "haustechnik", "sicherheitssysteme", "smarthome-systeme", "klimaanlagen", "lüftungssysteme", "heizungssysteme",
    "bauprojekte", "baumanagement", "baulogistik", "bauträger", "projektentwickler", "baukostenmanagement", "bausanierung",
    "stuckateur", "trockenbau", "isoliertechnik", "bodenverlegung", "wandverkleidungen", "deckenverkleidungen", "ausbauhandwerk",
    "batterieproduktion", "solarmodule", "stromspeicher", "e-mobilität", "ladestationen", "elektromobilität", "brennstoffzellen",
    "produktionstechnik", "supply chain management", "materialwissenschaften", "montageprozesse", "produktionsplanung",
    "maschinenwartung", "maschinenreparatur", "industrieservices", "ersatzteilmanagement", "anlagensicherheit",
    "pflegeberatung", "gesundheitstourismus", "homöopathie", "naturheilverfahren", "alternativmedizin", "ergotherapie",
    "wasseraufbereitung", "abwassertechnik", "kläranlagen", "trinkwasseranlagen", "wasserspeicher", "wassertests",
    "chemielabor", "lebensmittelanalytik", "biochemie", "pharmaforschung", "biotechnologische verfahren", "enzymtechnologie",
    "autoaufbereitung", "autopflege", "kfz-zubehör", "reifenhandel", "ersatzteile", "motorradwerkstätten", "tuningwerkstätten"
]

def get_city_info(postal_code):
    logger.info(f"Rufe Stadtinformationen für die Postleitzahl {postal_code} ab.")
    try:
        response = requests.get(
            f"http://api.geonames.org/postalCodeSearchJSON?postalcode={postal_code}&maxRows=1&username={GEONAMES_USER}"
        )
        response.raise_for_status()
        data = response.json()
        if not data['postalCodes']:
            raise ValueError("Keine Stadtinformationen gefunden.")
        location = data['postalCodes'][0]
        return {
            "city": location.get('placeName', 'Unbekannt'),
            "latitude": location.get('lat', 0),
            "longitude": location.get('lng', 0)
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Stadtinformationen: {e}")
        return {"city": "Unbekannt", "latitude": 0, "longitude": 0}

def get_weather_info(latitude, longitude):
    logger.info(f"Rufe Wetterinformationen für Breite {latitude}, Länge {longitude} ab.")
    try:
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_API_KEY}&units=metric&lang=de"
        )
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data['main']['temp'],
            "weather": data['weather'][0]['description']
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Wetterinformationen: {e}")
        return {"temperature": "unbekannt", "weather": "unbekannt"}

def analyze_idea(idea_text):
    logger.info("Starte Analyse der Geschäftsidee.")
    show_progress("Analysiere die Geschäftsidee...")
    try:
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=(
                f"Erstelle eine vollständige, detaillierte Marktanalyse basierend auf folgender Geschäftsidee: \n" 
                f"'{idea_text}'\n\n"
                "Die Analyse sollte beinhalten: \n"
                "Chancen und Risiken am Markt\n"
                "Relevante Zielgruppen\n"
                "Markteintrittsbarrieren und Konkurrenz\n"
                "Wachstumschancen im ersten und dritten Geschäftsjahr\n"
                "Eine abschließende Bewertung, ob diese Idee auf dem Markt bestehen kann."
            ),
            max_tokens=2000,
            temperature=0.6
        )
        feedback_text = response.generations[0].text.strip()
        return feedback_text
    except Exception as e:
        logger.error(f"Fehler bei der Analyse der Geschäftsidee: {str(e)}")
        return f"Fehler bei der Analyse der Geschäftsidee: {str(e)}"

def get_place_details(place_id):
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=website&key={GOOGLE_API_KEY}"
        )
        response.raise_for_status()
        data = response.json().get('result', {})
        return data.get('website', 'Keine Website')
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Details für Ort {place_id}: {e}")
        return 'Keine Website'

def extract_relevant_keywords(idea_text):
    # Suche nach definierten Branchen-Keywords in der Geschäftsidee
    found_keywords = [keyword for keyword in KEYWORD_CATEGORIES if re.search(rf"\b{keyword}\b", idea_text.lower())]
    if not found_keywords:
        # Fallback auf allgemeine Begriffe, wenn keine spezifischen Keywords gefunden werden
        found_keywords = ["handwerksbetrieb", "bau", "fertigung"]
    return found_keywords

def get_top_competitors(idea, latitude, longitude):
    logger.info(f"Suche nach Konkurrenten im Umkreis von 35 km basierend auf der Geschäftsidee.")
    show_progress("Suche nach Konkurrenten...")
    keywords = extract_relevant_keywords(idea)  # Extrahiere relevante Keywords
    competitors = []

    try:
        for keyword in keywords:
            logger.info(f"Suche mit Keyword: {keyword}")
            response = requests.get(
                f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=35000&keyword={keyword}&key={GOOGLE_API_KEY}"
            )
            response.raise_for_status()
            places = response.json().get('results', [])
            logger.info(f"{len(places)} Ergebnisse gefunden mit dem Suchbegriff '{keyword}'")
            for place in places:
                place_id = place.get('place_id', '')
                website = get_place_details(place_id) if place_id else 'Keine Website'
                competitors.append({
                    "name": place['name'],
                    "address": place.get('vicinity', 'Keine Adresse'),
                    "website": website,
                    "rating": place.get('rating', 'Keine Bewertung'),
                    "user_ratings_total": place.get('user_ratings_total', 0)
                })
        # Gib die besten 10 Konkurrenten zurück
        return competitors[:10] if competitors else []
    except Exception as e:
        logger.error(f"Fehler bei der Abfrage der Konkurrenten: {e}")
        return []

def analyze_success_probability(competitors):
    logger.info("Berechne Erfolgswahrscheinlichkeit.")
    if not competitors:
        return "Niedrig - Keine Konkurrenten gefunden."

    avg_rating = sum([c['rating'] for c in competitors if isinstance(c['rating'], (int, float))]) / len(competitors)
    probability = min(100, max(30, avg_rating * 15))
    return f"{probability:.2f}%"

def generate_detailed_business_plan(idea_text, competitors, success_probability):
    logger.info("Erstelle einen detaillierten Geschäftsplan.")
    show_progress("Erstelle Geschäftsplan...")
    try:
        competitors_section = ""
        if competitors:
            competitors_section = "\n\nTop 10 Konkurrenten im Markt: \n" + "\n".join(
                [f"- {c['name']} (Adresse: {c['address']}, Bewertung: {c['rating']} Sterne, Website: {c['website']})" for c in competitors]
            )
        
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=(
                f"Erstelle einen umfassenden Geschäftsplan für ein Unternehmen mit der folgenden Geschäftsidee: \n" 
                f"'{idea_text}'. \n\n"
                f"Die Erfolgswahrscheinlichkeit beträgt {success_probability}.\n"
                "Berücksichtige die folgenden Punkte im Geschäftsplan: \n"
                "Unternehmensstrategie und Vision \n"
                "Zielmarkt und Zielgruppe \n"
                "Marketing- und Vertriebsstrategien \n"
                "Betriebliches Management und Schlüsselressourcen \n"
                "Finanzplan (einschließlich Kostenaufstellung und Kapitalbedarf) \n"
                "Wettbewerbsanalyse" + competitors_section
            ),
            max_tokens=1500,
            temperature=0.6
        )
        business_plan = response.generations[0].text.strip()
        return clean_text(business_plan)
    except Exception as e:
        logger.error(f"Fehler bei der Erstellung des Geschäftsplans: {str(e)}")
        return f"Fehler bei der Erstellung des Geschäftsplans: {str(e)}"

def calculate_success_probability(competitors, market_risks=0.2):
    logger.info("Berechne die Erfolgswahrscheinlichkeit basierend auf den Konkurrenzdaten.")
    show_progress("Berechne Erfolgswahrscheinlichkeit...")
    if not competitors:
        return "Keine Konkurrenten gefunden. Erfolgswahrscheinlichkeit kann nicht berechnet werden."

    # Durchschnittliche Bewertung der Konkurrenten berechnen
    avg_rating = sum([c['rating'] for c in competitors]) / len(competitors)
    # Erfolgswahrscheinlichkeit basierend auf Bewertung und Marktrisiko
    probability = max(0, (avg_rating / 5) * (1 - market_risks) * 100)
    return f"{probability:.2f}% Erfolgswahrscheinlichkeit basierend auf Marktanalyse."

def generate_detailed_cost_estimation(idea_text):
    logger.info("Erstelle eine detaillierte Kostenaufstellung.")
    show_progress("Erstelle Kostenaufstellung...")
    try:
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=(
                f"Erstelle eine detaillierte Kostenaufstellung für ein Unternehmen basierend auf dieser Geschäftsidee: '{idea_text}'. \n\n"
                "Berücksichtige die folgenden Punkte: \n"
                "Büro- oder Ladenmiete \n"
                "Gehälter der Mitarbeiter (inkl. benötigter Fachkräfte) \n"
                "Material- oder Produktionskosten \n"
                "Marketing- und Werbebudget \n"
                "IT- und Verwaltungsinfrastruktur \n"
                "Sonstige laufende Kosten und Anlaufkosten \n"
                "Berechne die durchschnittlichen jährlichen Kosten und liefere eine geschätzte Kostentabelle."
            ),
            max_tokens=1200,
            temperature=0.7
        )
        cost_estimation = response.generations[0].text.strip()
        return clean_text(cost_estimation)
    except Exception as e:
        logger.error(f"Fehler bei der Erstellung der Kostenaufstellung: {str(e)}")
        return f"Fehler bei der Erstellung der Kostenaufstellung: {str(e)}"