from flask import Flask, request, jsonify, render_template
import logging
from services import (
    get_city_info, get_weather_info, analyze_idea,
    get_top_competitors, analyze_success_probability,
    generate_detailed_business_plan
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data or 'idea' not in data or 'postal_code' not in data:
        return jsonify({"error": "Geschäftsidee oder Postleitzahl fehlt"}), 400

    idea = data['idea']
    postal_code = data['postal_code']
    try:
        logger.info(f"Verarbeite Geschäftsidee: {idea} für Postleitzahl: {postal_code}")

        # Standortinformationen abrufen
        city_info = get_city_info(postal_code)
        if not city_info or city_info['city'] == 'Unbekannt':
            return jsonify({"error": "Konnte keine Stadtinformationen finden."}), 400

        # Wetterinformationen abrufen
        weather_info = get_weather_info(city_info['latitude'], city_info['longitude'])

        # Geschäftsidee analysieren
        feedback = analyze_idea(idea)

        # Top-Konkurrenten finden
        competitors = get_top_competitors(idea, city_info['latitude'], city_info['longitude'])

        # Erfolgswahrscheinlichkeit berechnen
        success_probability = analyze_success_probability(competitors)

        # Geschäftsplan generieren
        business_plan = generate_detailed_business_plan(idea, competitors, success_probability)

        return jsonify({
            "feedback": feedback,
            "competitors": competitors,
            "success_probability": success_probability,
            "business_plan": business_plan,
            "weather": weather_info
        })
    except Exception as e:
        logger.error(f"Fehler während der Analyse: {str(e)}")
        return jsonify({"error": f"Interner Serverfehler: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
