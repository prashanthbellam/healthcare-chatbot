import pandas as pd
from flask import Flask, request, jsonify, session
from flask_session import Session

class HealthcareChatbot:
    def __init__(self):
        # Predefined lists for entity extraction
        self.locations = ["New York", "Los Angeles", "Chicago"]
        self.specialties = ["Cardiology", "Dermatology", "Pediatrics"]

    def classify_intent(self, query):
        """Classify the user's intent based on keywords."""
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["hospital", "doctor", "clinic", "specialist"]):
            return "request_hospital_recommendation"
        elif any(keyword in query_lower for keyword in ["book", "schedule", "appointment"]):
            return "book_appointment"
        else:
            return "unknown"

    def extract_entities(self, query):
        """Extract location and specialty from the query."""
        query_lower = query.lower()
        location = next((loc for loc in self.locations if loc.lower() in query_lower), None)
        specialty = next((spec for spec in self.specialties if spec.lower() in query_lower), None)
        return location, specialty

    def recommend_hospital(self, location, specialty):
        """Recommend hospitals based on location and specialty."""
        # Assume hospitals.csv has columns: name, location, specialty, address, phone
        try:
            hospitals = pd.read_csv("hospitals.csv")
            filtered = hospitals[(hospitals['location'].str.lower() == location.lower()) &
                                 (hospitals['specialty'].str.lower() == specialty.lower())]
            if filtered.empty:
                return "No hospitals found matching your criteria."
            return filtered[['name', 'address', 'phone']].to_dict('records')
        except FileNotFoundError:
            return "Hospital data not available. Please ensure 'hospitals.csv' exists."

    def book_appointment(self, hospital_id, user_id, time_slot):
        """Simulate booking an appointment."""
        # Placeholder for an actual API call
        return f"Appointment booked successfully for hospital ID {hospital_id} at {time_slot}."

# Flask application setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
chatbot = HealthcareChatbot()

@app.route('/', methods=['GET'])
def index():
    """Display a welcome message."""
    return "Welcome to the Healthcare Chatbot"

@app.route('/chat', methods=['POST'])
def chat():
    """Handle user queries and manage conversation state."""
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
            else:
                session['state'] = 'awaiting_location'
                response = "Please specify your location."
        elif intent == "book_appointment":
            # Simplified: assumes all details are provided or hardcoded
            hospital_id = "H123"  # In practice, extract from query or context
            user_id = "U456"      # Should come from user session/auth
            time_slot = "2023-10-15 10:00"  # Extract from query in a real scenario
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
        location = session['location']
        hospitals = chatbot.recommend_hospital(location, specialty)
        response = f"Here are some hospitals in {location} for {specialty}: {hospitals}"
        session['state'] = 'start'

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
