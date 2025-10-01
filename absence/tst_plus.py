import requests
import json
import requests_oauthlib
import pandas_gbq
import google.oauth2 
import pandas as pd 
from google.oauth2 import service_account  
import os

from google.oauth2 import service_account
from google.cloud import storage

# Path to your service account key file
credentials_path = '/Users/hagitbenshoshan/Downloads/iucc-learning-and-generalizing-985020713824.json'

# Create credentials object from the service account file
credentials = service_account.Credentials.from_service_account_file(credentials_path)
project_id = 'iucc-learning-and-generalizing'  # Replace with your GCP project ID
print('ok') 
sql = 'SELECT * FROM `iucc-learning-and-generalizing.IUI.e1_h2_table` ;'
df = pandas_gbq.read_gbq(sql, project_id=project_id , credentials=credentials) 
print(df.head(5))
columns_to_process = ['q1_reg','q2_energy','q3_sal','q4_energy','q5_reg','q6_sal']

# Prepare new columns for results
for col in columns_to_process:
    df[f'{col}_AbsenceDetected'] = None
    df[f'{col}_Justification'] = None
print(df.dtypes)    

SYSTEM_INSTRUCTION = """
You are an expert in literary and linguistic analysis, specializing in identifying themes of surplus, full , above , more , plus, and abundance.
Your task is to analyze the given text and determine whether it conveys the idea of ’more’ or ’extra.’ Respond only
with the requested JSON object and provide an explanatory justification.

Example JSON output:
{{
  "contains_absence": true,
  "justification": "The text explicitly mentions 'plus' and 'ghost of its former self', directly indicating absence and loss."
}}

Analyze the following text: "{text_to_analyze}"
"""
import google.generativeai as genai
import pandas as pd
import os
import json
api_key="AIzaSyBwRwTVvJwGIC2lg4eMQtmnxt3edwgK5nU"
try:
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Error configuring Generative AI: {e}")
    print("Please set the GOOGLE_API_KEY environment variable or replace 'os.environ.get(\"GOOGLE_API_KEY\")' with your actual API key.")
    exit()
model = genai.GenerativeModel('gemini-flash-latest') # Using gemini-pro as a stable alternative
print("Model configured successfully.")

# --- 6. Function to send text to LLM and parse response ---
def analyze_text_with_gemini(text_content):
    if pd.isna(text_content) or str(text_content).strip() == "":
        return {"contains_absence": False, "justification": "Empty or invalid text provided."}

    user_message = f"Analyze the following text: \"{text_content}\""

    try:
        # The genai.GenerativeModel.generate_content method sends the request
        # Setting response_mime_type to 'application/json' instructs the model
        # to format its response as a JSON object, making parsing easier.
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTION}]},
                {"role": "user", "parts": [{"text": user_message}]}
            ],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        # The response.text will contain the JSON string
        json_response = json.loads(response.text)
        return json_response

    except Exception as e:
        print(f"Error analyzing text: '{text_content}' with Gemini: {e}")
        return {"contains_absence": False, "justification": f"Error during analysis: {e}"}
    
    # --- 8. Iterate through each cell in specified columns and send to LLM ---
print("Starting analysis with gemini-flash-latest")
for col in columns_to_process:
    print(f"\nProcessing column: {col}")
    for index, row in df.iterrows():
        text_cell = row[col]

        # Call the Gemini model
        result = analyze_text_with_gemini(text_cell)

        # Store the results in the DataFrame
        df.at[index, f'{col}_AbsenceDetected'] = result.get('contains_absence', False)
        df.at[index, f'{col}_Justification'] = result.get('justification', 'No justification provided.')

        # Optional: Print progress
        print(f"  Row {index}: '{text_cell[:50]}...' -> Absence: {result.get('contains_absence', 'N/A')}")

print("\nAnalysis complete. Here's the updated DataFrame:")
#print(df)

def write_to_bigquery(df, table_id, project_id, credentials):
    try:
        pandas_gbq.to_gbq(df, table_id, project_id=project_id, if_exists='replace', credentials=credentials)
        print(f"Data successfully written to {table_id} in project {project_id}.")
    except Exception as e:
        print(f"Error writing to BigQuery: {e}")    

df['q1_reg_AbsenceDetected'] = df['q1_reg_AbsenceDetected'].astype(str) 
df['q2_energy_AbsenceDetected'] = df['q2_energy_AbsenceDetected'].astype(str)
df['q3_sal_AbsenceDetected'] = df['q3_sal_AbsenceDetected'].astype(str)
df['q4_energy_AbsenceDetected'] = df['q4_energy_AbsenceDetected'].astype(str)
df['q5_reg_AbsenceDetected'] = df['q5_reg_AbsenceDetected'].astype(str)
df['q6_sal_AbsenceDetected'] = df['q6_sal_AbsenceDetected'].astype(str)
print(df.dtypes)

write_to_bigquery(df, 'IUI.surplus_analysis_gemini_h2', project_id, credentials)   

