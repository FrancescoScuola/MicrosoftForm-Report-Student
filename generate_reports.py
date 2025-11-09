# report.py
#
# Final report generation script.
# The answer key file is now OPTIONAL.
#
# Usage (with answer key):
# python report.py "student_data.csv" "answer_key.csv"
#
# Usage (without answer key):
# python report.py "student_data.csv"
#

import pandas as pd
import sys
import os
from datetime import datetime
from html import escape # Used to safely print HTML characters in PDF

# Try to import the reportlab library
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
except ImportError:
    print("Error: The 'reportlab' library is not installed.")
    print("Please activate your virtual environment and run:")
    print("pip install reportlab")
    sys.exit(1)

# ==========================================================
#  SCRIPT SETTINGS
# ==========================================================
# Column names from the student data file
STUDENT_NAME_COLUMN = "Nome e Cognome"
POINTS_PREFIX = "Points - "
CALCULATED_PREFIX = "CALCOLO - " 
FINAL_SCORE_COLUMN = "Punteggio_Finale_Corretto"
FINAL_GRADE_COLUMN = "Voto_su_10"

# Column names from the answer key file
ANSWER_KEY_QUESTION_COL = "Domanda"
ANSWER_KEY_ANSWER_COL = "RispostaCorretta"

# PDF Output settings
OUTPUT_FOLDER = "Student_Reports_Final"
# ==========================================================


def load_answer_key(key_file_path):
    """
    Reads the answer key CSV and returns a dictionary
    for fast lookup: {question_text: correct_answer_text}
    """
    try:
        # Use utf-8-sig to handle the BOM from Excel
        df_key = pd.read_csv(key_file_path, sep=';', encoding='utf-8-sig')
        
        if ANSWER_KEY_QUESTION_COL not in df_key.columns or ANSWER_KEY_ANSWER_COL not in df_key.columns:
            print(f"  > Error: Key file '{key_file_path}' must contain")
            print(f"  > '{ANSWER_KEY_QUESTION_COL}' and '{ANSWER_KEY_ANSWER_COL}' columns.")
            return None
            
        # Fill empty answers with a placeholder
        df_key[ANSWER_KEY_ANSWER_COL] = df_key[ANSWER_KEY_ANSWER_COL].fillna(pd.NA)
        
        return pd.Series(df_key[ANSWER_KEY_ANSWER_COL].values, 
                         index=df_key[ANSWER_KEY_QUESTION_COL]).to_dict()
    except Exception as e:
        print(f"  > Error reading answer key file '{key_file_path}': {e}")
        return None

def find_question_list(df_columns):
    """
    Robustly scans the data columns and identifies the list of questions
    by finding matching (Question, "Points - " + Question) pairs.
    """
    questions = []
    # Create a set of all column names for very fast lookup
    all_cols_set = set(df_columns)
    
    for col_name in df_columns:
        # A column is a "Question" if its corresponding "Points -" column exists
        if f"{POINTS_PREFIX}{col_name}" in all_cols_set:
            
            # We also check that the column itself is not a special one
            if not col_name.startswith((POINTS_PREFIX, CALCULATED_PREFIX, "Feedback - ")):
                 questions.append(col_name)
                 
    return questions


def create_student_pdf(pdf_path, student_data, question_list, answer_key):
    """
    Creates a single PDF file for one student.
    'answer_key' is a dictionary. If it's empty, correct answers are skipped.
    """
    
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    
    # Define text styles
    styles = getSampleStyleSheet()
    style_h1 = styles['h1']
    style_body = styles['BodyText']
    style_body.fontSize = 11
    style_body.leading = 14  # Line spacing

    style_question = ParagraphStyle('Question', parent=styles['h3'], fontSize=12, spaceAfter=4)
    
    style_correct_answer = ParagraphStyle(
        'CorrectAnswer',
        parent=style_body,
        textColor=colors.HexColor('#228B22'), # ForestGreen
        fontName='Helvetica-Bold',
        leftIndent=1*cm,
        spaceBefore=4
    )

    # --- 1. PDF Header ---
    student_name = student_data.get(STUDENT_NAME_COLUMN, "Unknown Student")
    story.append(Paragraph(f"Test Report: {escape(student_name)}", style_h1))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", style_body))
    
    # --- 2. Summary Scores ---
    story.append(Spacer(1, 1 * cm))
    if FINAL_SCORE_COLUMN in student_data:
        score = student_data[FINAL_SCORE_COLUMN]
        grade = student_data.get(FINAL_GRADE_COLUMN, "N/A")
        story.append(Paragraph(f"<b>Final Calculated Score:</b> {score}", style_body))
        story.append(Paragraph(f"<b>Final Grade (out of 10):</b> {grade}", style_body))
    story.append(Spacer(1, 1.5 * cm))

    # --- 3. List of Questions and Answers ---
    for question_text in question_list:
        
        student_answer = student_data.get(question_text)
        calc_col_name = f"{CALCULATED_PREFIX}{question_text}"
        calculated_score = pd.to_numeric(student_data.get(calc_col_name), errors='coerce')
        
        if pd.isna(student_answer) or str(student_answer).strip() == '':
            answer_display = "<i>(No answer given)</i>"
        else:
            answer_display = escape(str(student_answer))

        story.append(Paragraph(escape(question_text), style_question))
        story.append(Paragraph(f"<b>Your Answer:</b> {answer_display}", style_body))
        story.append(Paragraph(f"<b>Calculated Score:</b> {calculated_score}", style_body))

        # --- KEY LOGIC (Handles both requests) ---
        # If score is less than 1 (wrong) AND the answer_key is not empty
        if calculated_score < 1 and answer_key:
            correct_answer = answer_key.get(question_text)
            
            # This handles request #2:
            # If a correct answer was found AND it's not empty
            if correct_answer and pd.notna(correct_answer):
                story.append(Paragraph(
                    f"<b>Correct Answer:</b> {escape(str(correct_answer))}", 
                    style_correct_answer
                ))
            else:
                # Key exists, but this specific question is missing from it
                print(f"  > Warning: No key found for question: '{question_text}'")

        story.append(Spacer(1, 1 * cm)) # Space between questions

    # Build the PDF
    try:
        doc.build(story)
        print(f"  > OK: Created {pdf_path}")
    except Exception as e:
        print(f"  > ERROR creating PDF for {student_name}: {e}")


def main():
    """
    Main function to run the report generation.
    The answer key file (sys.argv[2]) is now optional.
    """
    # --- 1. Check arguments ---
    if len(sys.argv) < 2:
        print("Error: Missing arguments.")
        print("Usage: python report.py \"<student_data_file.csv>\" [optional_answer_key.csv]")
        print("\nExample (with key):")
        print("python report.py \"grades.csv\" \"key.csv\"")
        print("\nExample (without key):")
        print("python report.py \"grades.csv\"")
        sys.exit(1)
        
    student_file = sys.argv[1]
    key_file = None
    answer_key_dict = {}  # Default to an empty dictionary

    # --- 2. Check for optional answer key ---
    if len(sys.argv) >= 3:
        key_file = sys.argv[2]
        print(f"Attempting to load answer key from: '{key_file}'")
        if not os.path.exists(key_file):
            print(f"  > Warning: Key file not found at '{key_file}'.")
            print("  > Proceeding without correct answers.")
        else:
            answer_key_dict = load_answer_key(key_file)
            if answer_key_dict is None:
                print("  > Error loading key file. Proceeding without correct answers.")
                answer_key_dict = {} # Reset to empty
            else:
                print(f"  > Successfully loaded {len(answer_key_dict)} correct answers.")
    else:
        print("No answer key file provided.")
        print("Generating reports without showing correct answers.")

    # --- 3. Load Student Data ---
    if not os.path.exists(student_file):
        print(f"Error: Student data file not found: '{student_file}'")
        sys.exit(1)
        
    print(f"Loading student data from: '{student_file}'")
    try:
        df_students = pd.read_csv(student_file, sep=';', encoding='utf-8-sig', low_memory=False)
    except Exception as e:
        print(f"Error reading student file: {e}")
        sys.exit(1)
    
    df_students = df_students.dropna(axis=1, how='all')

    # --- 4. Find all questions ---
    print("Identifying questions from student data...")
    question_list = find_question_list(df_students.columns)
    if not question_list:
        print("Error: No valid question/points pairs found in the student file.")
        print(f"Check if '{POINTS_PREFIX}' prefix is correct.")
        sys.exit(1)
    print(f"Found {len(question_list)} questions to report.")
    
    # --- 5. Create Output Folder ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"PDFs will be saved to: '{OUTPUT_FOLDER}'")

    # --- 6. Iterate and Generate PDFs ---
    if STUDENT_NAME_COLUMN not in df_students.columns:
        print(f"Error: Student name column '{STUDENT_NAME_COLUMN}' not found.")
        sys.exit(1)

    print("\nStarting PDF generation...")
    for index, student_row in df_students.iterrows():
        
        student_name = student_row.get(STUDENT_NAME_COLUMN)
        if pd.isna(student_name) or str(student_name).strip() == "":
            student_name = f"Student_ID_{index}"
            
        print(f"Processing report for: {student_name}")
        
        safe_name = student_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "").replace("*", "")
        pdf_file_name = f"Report - {safe_name}.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_file_name)
        
        # Pass the (possibly empty) answer_key_dict to the function
        create_student_pdf(pdf_path, student_row, question_list, answer_key_dict)

    print("\nAll reports generated successfully.")

# --- Run the main function ---
if __name__ == "__main__":
    main()