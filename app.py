from flask import Flask, request, jsonify, render_template, send_file
import requests
import sqlite3
import random
import io
import os

app = Flask(__name__)

# Database file
db_file = "data.db"

# Mapping sheet names to display names
sheet_name_mapping = {
    "CivPro": "Civil Procedure",
    "ConLaw": "Constitutional Law",
    "Contracts": "Contracts",
    "CrimLaw-Pro": "Criminal Law & Procedure",
    "Evidence": "Evidence",
    "RealProperty": "Real Property",
    "Torts": "Torts"
}

# Function to fetch a random question from the database
def get_random_question():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM quiz_table")
    question_ids = [row[0] for row in cursor.fetchall()]

    question_id = random.choice(question_ids)

    cursor.execute("""
        SELECT id, question, choice1, choice2, choice3, choice4, correct_choice, correct_answer, sheet_name
        FROM quiz_table
        WHERE id = ?
    """, (question_id,))
    question_data = cursor.fetchone()

    conn.close()

    return {
        "id": question_data[0],
        "question": question_data[1],
        "choices": [
            ("A", question_data[2]),
            ("B", question_data[3]),
            ("C", question_data[4]),
            ("D", question_data[5])
        ],
        "correct_choice": question_data[6],
        "correct_answer": question_data[7],
        "sheet_name": sheet_name_mapping.get(question_data[8], question_data[8])
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_question', methods=['GET'])
def get_question():
    question_data = get_random_question()
    return jsonify(question_data)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    question_id = data['question_id']
    user_choice = data['user_choice']

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT question, correct_choice, correct_answer, sheet_name
        FROM quiz_table
        WHERE id = ?
    """, (question_id,))
    result = cursor.fetchone()
    question_text, correct_choice, correct_answer, sheet_name = result

    conn.close()

    correct = user_choice == correct_choice.strip()
    response = {
        "correct": correct,
        "correct_choice": correct_choice.strip(),
        "correct_answer": correct_answer.strip(),
        "sheet_name": sheet_name_mapping.get(sheet_name, sheet_name)
    }

    if not correct:
        # Call Ollama server to explain why the answer was incorrect
        explanation = get_explanation(question_text, user_choice)
        response["explanation"] = explanation

    return jsonify(response)

def get_explanation(question_text, user_choice):
    # Call Ollama server to get explanation
    url = "https://ai.mythicheroes.space/api/generate"
    prompt = f"Explain why the answer '{user_choice}' is incorrect for the question: '{question_text}'."
    payload = {
        "model": "ALIENTELLIGENCE/attorney2",
        "prompt": prompt,
        "stream": False
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("response", "No explanation available.")

# Add the Piper and Whisper routes here
@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    text = data['text']
    voice = os.getenv('VOICE_MODEL', 'en_US-lessac-medium.onnx')  # Use environmental variable for voice model
    url = "http://192.168.5.151:8042/api/tts"  # Piper TTS server URL

    payload = {
        "text": text,
        "voice": voice
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        audio_data = io.BytesIO(response.content)
        return send_file(audio_data, mimetype='audio/wav')
    else:
        return jsonify({"error": "Failed to generate speech"}), response.status_code

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    url = "https://sttx.mythicheroes.space/transcribe"
    files = {'audio': audio_file}
    response = requests.post(url, files=files)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
