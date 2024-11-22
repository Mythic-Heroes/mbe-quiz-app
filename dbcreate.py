import pandas as pd
import sqlite3

# File paths
excel_file = "data.xlsx"  # Replace with your Excel file name
db_file = "data.db"       # Name of the database file

# Read all sheets into a dictionary of DataFrames
all_sheets = pd.read_excel(excel_file, sheet_name=None)

# Connect to SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create table in the database (if not already created)
cursor.execute("""
CREATE TABLE IF NOT EXISTS quiz_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    choice1 TEXT,
    choice2 TEXT,
    choice3 TEXT,
    choice4 TEXT,
    correct_choice TEXT,
    correct_answer TEXT,
    sheet_name TEXT
)
""")

# Process each sheet
for sheet_name, df in all_sheets.items():
    print(f"Processing sheet: {sheet_name}")

    # Fill NaN values with empty strings to avoid insertion errors
    df.fillna("", inplace=True)

    # Determine the correct answer text based on the letter provided
    def get_correct_answer(row):
        if row["Answer"].strip() == "A":
            return row["A"].strip()
        elif row["Answer"].strip() == "B":
            return row["B"].strip()
        elif row["Answer"].strip() == "C":
            return row["C"].strip()
        elif row["Answer"].strip() == "D":
            return row["D"].strip()
        return ""

    # Apply the mapping function
    df["Correct Answer Text"] = df.apply(get_correct_answer, axis=1)
    
    # Debug: Print the DataFrame to verify correct mapping
    for index, row in df.iterrows():
        print(f"Row {index}: Question='{row['Question']}', Answer='{row['Answer']}', Correct Answer Text='{row['Correct Answer Text']}'")

    # Insert data from the current sheet into the database
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO quiz_table (question, choice1, choice2, choice3, choice4, correct_choice, correct_answer, sheet_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (row["Question"].strip(), row["A"].strip(), row["B"].strip(), row["C"].strip(), row["D"].strip(), row["Answer"].strip(), row["Correct Answer Text"].strip(), sheet_name))

# Commit and close the connection
conn.commit()
conn.close()

print(f"Data from {excel_file} has been successfully inserted into {db_file}.")
