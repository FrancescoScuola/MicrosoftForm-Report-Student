# create_answer_key.py
#
# This script reads a Microsoft Forms CSV export (with ; separator)
# and automatically generates an "_key.csv" file.
# It intelligently finds the correct answer for each question
# by locating the first student who scored '1' point.

import pandas as pd
import sys
import os

# ==========================================================
#  SETTINGS
# ==========================================================
# The prefix used by Forms for points columns
POINTS_PREFIX = "Points - "
# The prefix for feedback columns (used to skip columns correctly)
FEEDBACK_PREFIX = "Feedback - "

# The column names to be created in the output key file
KEY_QUESTION_COL = "Domanda"
KEY_ANSWER_COL = "RispostaCorretta"
# ==========================================================


def generate_automatic_key(input_file):
    """
    Reads a Forms CSV, identifies questions, and searches all student
    rows to find a correct answer (where Points=1) to auto-fill the key.
    """
    
    # --- 1. Check file and set up output path ---
    if not os.path.exists(input_file):
        print(f"Error: Input file was not found: '{input_file}'")
        return

    # Create the output file name, e.g., "sicurezzaDSA_key.csv"
    file_stem, file_ext = os.path.splitext(input_file)
    output_file = f"{file_stem}_key.csv"
    
    # --- 2. Read the CSV file ---
    try:
        print(f"Reading file: '{input_file}'...")
        try:
            # Try with UTF-8 first
            df = pd.read_csv(input_file, sep=';', encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            # Fallback for older Excel/Windows encoding
            print("UTF-8 failed, trying 'latin-1' encoding...")
            df = pd.read_csv(input_file, sep=';', encoding='latin-1', low_memory=False)

        # Clean any completely empty columns
        df = df.dropna(axis=1, how='all')

    except Exception as e:
        print(f"Fatal Error reading file: {e}")
        return

    # --- 3. Identify questions and find correct answers ---
    print("Phase 2: Identifying questions and searching for correct answers...")
    
    # This list will hold our dictionary data for the final key file
    key_data = []
    
    columns = list(df.columns)
    num_columns = len(columns)
    questions_found = 0
    answers_found = 0
    i = 0  # We use a while loop to manually skip columns

    while i < num_columns:
        question_col_name = columns[i]
        expected_points_col = f"{POINTS_PREFIX}{question_col_name}"
        
        # Check if the next column is the 'Points' column for this one
        if (i + 1 < num_columns and columns[i+1] == expected_points_col):
            
            # --- This is a Question! ---
            questions_found += 1
            question_series = df[question_col_name]
            points_series = pd.to_numeric(df[expected_points_col], errors='coerce')
            
            correct_answer_found = "" # Default to empty string
            
            # --- THE SMART LOGIC ---
            # Try to find the first student who scored 1 point
            try:
                # (points_series == 1) creates a True/False series
                # .idxmax() finds the *first* index that is 'True'
                is_correct_series = (points_series == 1)
                first_correct_index = is_correct_series.idxmax()
                
                # We must check if the index we found *actually* has a '1'
                # because idxmax() returns index 0 if all are 'False'
                if is_correct_series[first_correct_index]:
                    # Success! Get the answer from that student's row
                    correct_answer_found = question_series[first_correct_index]
                    print(f"  > Q: '{question_col_name[0:45]}...' -> Answer FOUND")
                    answers_found += 1
                else:
                    # No student scored '1' for this question
                    raise ValueError("No '1' found in points column")
                    
            except Exception as e:
                # This catches errors or the "No '1' found" case
                print(f"  > Q: '{question_col_name[0:45]}...' -> WARNING: No correct answer found (no '1').")
                correct_answer_found = "" # Leave it blank
            
            # Add the data for our key file
            key_data.append({
                KEY_QUESTION_COL: question_col_name,
                KEY_ANSWER_COL: correct_answer_found
            })
            
            # Now, skip the columns we've processed
            expected_feedback_col = f"{FEEDBACK_PREFIX}{question_col_name}"
            if (i + 2 < num_columns and columns[i+2] == expected_feedback_col):
                i += 3 # Skip (Question, Points, Feedback)
            else:
                i += 2 # Skip (Question, Points)
        else:
            # This is not a question column, move to the next
            i += 1

    print(f"\nIdentified {questions_found} total questions.")
    print(f"Automatically filled {answers_found} correct answers.")

    # --- 4. Create and Save the Key File ---
    if not key_data:
        print("Error: No valid question columns were found.")
        return

    print(f"Phase 3: Creating key file at '{output_file}'...")
    
    # Create the final DataFrame from our list of dictionaries
    df_key = pd.DataFrame(key_data)
    
    # Save the file
    # use 'utf-8-sig' to add a BOM, which helps Excel open it
    # with correct characters (like 'è', 'à')
    df_key.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';')
    
    print("\nOperation complete!")
    print(f"File saved: '{output_file}'")
    print("IMPORTANT: Please open this file in Excel to check.")
    print("You *must* manually fill in any 'RispostaCorretta' cells that are still blank.")

# --- This runs the script from the command line ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: You must provide the CSV file name as an argument.")
        print(f"Usage: python {sys.argv[0]} \"<your_forms_file.csv>\"")
        print(f"Example: python {sys.argv[0]} \"sicurezzaDSA.csv\"")
    else:
        input_file_name = sys.argv[1]
        generate_automatic_key(input_file_name)