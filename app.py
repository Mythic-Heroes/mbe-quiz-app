import gradio as gr
import sqlite3
import random

# Database file
db_file = "data.db"

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
    
    # Debug: Print the fetched question data
    print(f"Fetched question data: {question_data}")
    
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
        "sheet_name": question_data[8]
    }

# Function to handle quiz interaction
def check_answer(user_choice, question_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT correct_choice, correct_answer, sheet_name
        FROM quiz_table
        WHERE id = ?
    """, (question_id,))
    result = cursor.fetchone()
    correct_choice, correct_answer, sheet_name = result
    
    conn.close()
    
    # Extract the letter part of the user choice
    user_choice_letter = user_choice.split('.')[0].strip()
    
    # Strip whitespace from correct choice and correct answer
    correct_choice = correct_choice.strip()
    correct_answer = correct_answer.strip()
    
    # Debug: Print the correct choice, correct answer, and user choice
    print(f"Comparing user choice and correct choice")
    print(f"User choice letter: '{user_choice_letter}'")
    print(f"Correct choice: '{correct_choice}'")
    print(f"Correct answer: '{correct_answer}'")
    
    # Compare user choice letter to correct choice
    if user_choice_letter == correct_choice:
        feedback = "Correct!"
    else:
        feedback = f"Incorrect. The correct answer was: {correct_choice} - {correct_answer}."
    
    if sheet_name:
        feedback += f"\nCategory: {sheet_name}"
    
    return feedback

# Function to load the next question
def next_question():
    question_data = get_random_question()
    choices = [f"{label}. {text}" for label, text in question_data["choices"]]
    return (
        question_data["question"],
        gr.update(choices=choices),
        question_data["id"]
    )

# Gradio Interface
with gr.Blocks(title="Bar Exam Prep") as quiz_app:
    question_id_state = gr.State()

    with gr.Row():
        question_display = gr.Textbox(label="Question", interactive=False)
    with gr.Row():
        choices_radio = gr.Radio(label="Choices", choices=[], interactive=True)
    with gr.Row():
        feedback_display = gr.Textbox(label="Answer", interactive=False)
    with gr.Row():
        submit_button = gr.Button("Submit")
        next_button = gr.Button("Next Question")
    
    submit_button.click(
        fn=check_answer,
        inputs=[choices_radio, question_id_state],
        outputs=feedback_display
    )
    
    next_button.click(
        fn=next_question,
        inputs=[],
        outputs=[question_display, choices_radio, question_id_state]
    )
    
    quiz_app.load(
        fn=next_question,
        inputs=[],
        outputs=[question_display, choices_radio, question_id_state]
    )

quiz_app.launch()
