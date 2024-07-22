import json
import argparse
import requests
from datetime import datetime, timezone
from typing import Optional
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import re
import os


def main(prompt_text):
    llm = ChatOllama(model="llama3")

    messages = [
        HumanMessage(content=f"Extract the start and end dates and concept from this prompt: '{prompt_text}'.\n" +
        "Follow these rules:\n" +
        "The concept should be one of: 'average_carbon_intensity', 'maximum_carbon_intensity', 'minimum_carbon_intensity', or 'predict_least_carbon'. The concept is based on the content of the prompt. For example, if the prompt is about finding the highest carbon emissions or producing, USE ONLY 'maximum_carbon_intensity'. If the prompt is about finding the average level of emissions, it should be 'average_carbon_intensity'.\n" +
        "1. For specific dates like 'April 2022', assume start and end dates as the first and last day of that month.\n" +
        "2. For month and year, use the first and last day of the month.\n" +
        "3. For only a year, use January 1st and December 31st of that year.\n" +
        "4. For relative terms like 'this year', use the current year’s start and end dates.\n" +
        "5. For 'next year', use the start and end dates of the upcoming year.\n" +
        "6. Ensure dates are formatted as YYYY-MM-DDTHH:MM:SS.SSSZ." +
        "7. Identify the concept as one of average_carbon_intensity, maximum_carbon_intensity, minimum_carbon_intensity, or predict_least_carbon.\n" +
        "Provide the response strictly in the format with 1 line and no precusor saying 'Here is the extracted information':\n" +
        "Start Date: YYYY-MM-DDTHH:MM:SS.SSSZ End Date: YYYY-MM-DDTHH:MM:SS.SSSZ Concept: [concept]")
    ]

prompt = ChatPromptTemplate.from_messages(messages)

chain = prompt | llm | StrOutputParser()

input_data = {}

response = chain.invoke(input_data)
    result = re.search(
    r"Start Date:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s*End Date:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s*Concept:\s*(\w+)",
    response
    )
    if result:
        start_date = result.group(1)
        end_date = result.group(2)
        concept = result.group(3)
        return start_date, end_date, concept
    else:
        print("Could not extract dates and concept.")
        return None, None, None


def is_date_range_valid(start_date: Optional[datetime], end_date: Optional[datetime], last_available_date: datetime) -> bool:
    if end_date:
        return end_date <= last_available_date
    return True 
def load_last_available_date(file_path: str) -> datetime:
    with open(file_path, 'r') as f:
        data = json.load(f)

        data_entries = data.get('data', [])
        
        if not data_entries:
            raise ValueError("No data entries found in the JSON file.")

        datetime_strings = [entry['datetime'] for entry in data_entries]
        
        datetime_objects = [datetime.fromisoformat(dt.replace('Z', '+00:00')).replace(tzinfo=None) for dt in datetime_strings]
        
        last_available_date = max(datetime_objects)
        
        return last_available_date

def call_api(closest_concept: str, ts_id: str, start_str: str, end_str: str, last_available_date: datetime):
    if not is_date_range_valid(start_date, end_date, last_available_date):
        closest_concept = 'predict_least_carbon'
        endpoint = "/predict_least_carbon/"
        params = {"ts_id": ts_id}
    else:
        if closest_concept == 'maximum_carbon_intensity':
            endpoint = "/max/"
            params = {"ts_id": ts_id, "start": start_str, "end": end_str}
        elif closest_concept == 'average_carbon_intensity':
            endpoint = "/average/"
            params = {"ts_id": ts_id, "start": start_str, "end": end_str}
        elif closest_concept == 'minimum_carbon_intensity':
            endpoint = "/min/"
            params = {"ts_id": ts_id, "start": start_str, "end": end_str}
        elif closest_concept == 'predict_least_carbon':
            endpoint = "/predict_least_carbon/"
            params = {"ts_id": ts_id}
        else:
            raise ValueError("Unknown concept")
    
    url = f"http://localhost:8000{endpoint}"
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def format_output(prompt: str, result: dict) -> str:
    if 'average' in result:
        return f"Calling the function get_avg(id, start, end) will return {result['average']} Tons CO2e/GWh, on May 2020."
    elif 'max' in result:
        return f"Calling the function get_max(id, start, end) will return {result['max']} Tons CO2e/GWh, in 2021."
    elif 'min' in result:
        return f"Calling the function get_min(id, start, end) will return {result['min']} Tons CO2e/GWh, in 2021."
    elif 'predicted_value' in result:
        return f"Calling the function predict_least_carbon(id, start, end) will return {result['predicted_value']} Tons CO2e/GWh, for the upcoming year."
    else:
        return "No data available."

def process_prompt(prompt: str) -> str:
    last_available_date = load_last_available_date('data/caiso_carbon_intensity.json')
    
    start_date, end_date, closest_concept = main(prompt)
    ts_id = "caiso_carbon_intensity"
    
    if not start_date or not end_date or not closest_concept:
        return "Could not process the prompt."

    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=None)
    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=None)
    
    start_str = start_date.replace(tzinfo=timezone.utc).isoformat() if start_date else None
    end_str = end_date.replace(tzinfo=timezone.utc).isoformat() if end_date else None
    last_available_str = last_available_date.replace(tzinfo=timezone.utc).isoformat() if last_available_date else None
    return start_str, end_str, closest_concept, last_available_str

if __name__ == "__main__":
    prompt_text = os.getenv('PROMPT_TEXT', '')

    print(process_prompt(prompt_text))