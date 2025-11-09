# MicrosoftForm-Report-Student

A set of Python scripts to process CSV exports from Microsoft Forms quizzes.

## Features

* Calculates final grades based on custom rules (e.g., +1 for correct, -0.25 for wrong, 0 for no answer).
* Generates an individual PDF report for each student, named after them.

## How to Use

1.  Place your CSV export (using ';' as separator) in this folder.
2.  Install required libraries: `pip install pandas reportlab`
3.  Run the grade calculation:
    `python calculate_grades.py "your_file.csv"`
4.  Run the report generation using the new file:
    `python generate_reports.py "your_file_grades_calculated.csv"`