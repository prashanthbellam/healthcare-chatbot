import pandas as pd
from flask import Flask, request, jsonify, session
from flask_session import Session

class HealthcareChatbot:
    def __init__(self):
        try:
            self.hospitals = pd.read_csv("hospitals.csv")
            # Standardize column names
            self.hospitals.columns = [col.lower() for col in self.hospitals.columns]

            # Extract unique locations and specialties for entity matching
            self.locations = self.hospitals['location'].dropna().unique().tolist()
            self.specialties = self.hospitals['specialty'].dropna().unique().tolist()
        except FileNotFoundError:
            self.hospitals = pd.DataFrame()
            self.locations = []
            self.specialties = []

    def classify_intent(self, query):
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["hospital", "doctor", "clinic", "specialist"]):
            return "request_hospital_recommendation"
        elif any(keyword in query_lower for keyword in ["book", "schedule", "appointment"]):
            return "book_appointment"
        else:
            return "unknown"

    def extract_entities(self, query):
        query_lower = query.lower()
        location = next((loc for loc in self.locations if loc.lower() in query_lower), None)
        specialty = next((spec for spec in self.specialties if spec.lower() in query_lower), None)
        return location, specialty

    def recommend_hospital(self, location, specialty):
        if self.hospitals.empty:
            return "Hospital data not available. Please ensure 'hospitals.csv' exists."

        # Filter based on case-insensitive match
        filtered = self.hospitals[
            (self.hospitals['location'].str.lower() == location.lower()) &
            (self.hospitals['specialty'].str.lower() == specialty.lower())
        ]

        if filtered.empty:
            return "No hospitals found matching your criteria."

        return filtered[['name', 'address', 'phone']].to_dict('records')

    def book_appointment(self, hospital_id, user_id, time_slot):
        return f"Appointment booked successfully for hospital ID {hospital_id} at {time_slot}."

# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

chatbot = HealthcareChatbot()

@app.route('/', methods=['GET'])
def index():
    return "Welcome to the Healthcare Chatbot"

@app.route('/chat', methods=['POST'])
def chat():
    query = request.json.get('query', '')
    state = session.get('state', 'start')
    response = ""

    if state == 'start':
        intent = chatbot.classify_intent(query)
        if intent == "request_hospital_recommendation":
            location, specialty = chatbot.extract_entities(query)
            if location and specialty:
                hospitals = chatbot.recommend_hospital(location, specialty)
                response = f"Here are some hospitals in {location} for {specialty}: {hospitals}"
            elif not location:
                session['state'] = 'awaiting_location'
                response = "Please specify your location."
            elif not specialty:
                session['state'] = 'awaiting_specialty'
                session['location'] = location
                response = "Please specify the specialty you're looking for."
        elif intent == "book_appointment":
            hospital_id = "H123"
            user_id = "U456"
            time_slot = "2023-10-15 10:00"
            response = chatbot.book_appointment(hospital_id, user_id, time_slot)
        else:
            response = "I'm not sure how to help with that."

    elif state == 'awaiting_location':
        location = query
        session['location'] = location
        session['state'] = 'awaiting_specialty'
        response = "Now, what specialty are you looking for?"

    elif state == 'awaiting_specialty':
        specialty = query
        location = session.get('location')
        hospitals = chatbot.recommend_hospital(location, specialty)
        response = f"Here are some hospitals in {location} for {specialty}: {hospitals}"
        session['state'] = 'start'

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
