import json
import os
from datetime import datetime
from typing import Dict, Optional
import subprocess
from subprocess import Popen, PIPE
import ast
import pandas as pd
import statsmodels.api as sm
import requests
from collections import defaultdict

customer_preferences_db: Dict[str, Dict[str, str]] = {}

def load_data(file_path: str) -> list:
    file_path = file_path+".json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

    records = data.get('data', [])
    
    if not isinstance(records, list):
        raise ValueError("Invalid format: 'data' must be a list")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"Invalid record format: Each record must be a dictionary, found {type(record)}")
        if 'datetime' not in record or 'carbon_intensity' not in record:
            raise ValueError("Invalid record format: Each record must contain 'datetime' and 'carbon_intensity' keys")

    return records


def save_customer_preferences(cust_id: str, pref: dict) -> dict:
    # Store preferences in-memory (could be replaced by a database)
    customer_preferences_db[cust_id] = pref

    return {cust_id: customer_preferences_db[cust_id]}


def get_max(ts_id: str = 'caiso_carbon_intensity', start: str = '', end: str = '') -> int:
    try:
        # Convert start and end to datetime objects
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError("Invalid datetime format. Use ISO 8601 format.")

    try:
        data = load_data(f'data/{ts_id}')
    except Exception as e:
        raise RuntimeError("Error loading data: " + str(e))

    filtered_data = []
    for record in data:
        if start_dt <= datetime.fromisoformat(record['datetime'].replace('Z', '+00:00')) < end_dt:
            filtered_data.append(record)
    if not filtered_data:
        raise ValueError("No data available for the given range")

    return max(record['carbon_intensity'] for record in filtered_data)


def get_min(ts_id: str = 'caiso_carbon_intensity', start: str = '', end: str = '') -> int:
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError("Invalid datetime format. Use ISO 8601 format.")

    try:
        data = load_data(f'data/{ts_id}')
    except Exception as e:
        raise RuntimeError("Error loading data: " + str(e))

    filtered_data = []
    for record in data:
        if start_dt <= datetime.fromisoformat(record['datetime'].replace('Z', '+00:00')) < end_dt:
            filtered_data.append(record)
    if not filtered_data:
        raise ValueError("No data available for the given range")

    return min(record['carbon_intensity'] for record in filtered_data)

def get_avg(ts_id: str = 'caiso_carbon_intensity', start: str = '', end: str = ''):
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError("Invalid datetime format. Use ISO 8601 format.")

    try:
        data = load_data(f'data/{ts_id}')
    except Exception as e:
        raise RuntimeError("Error loading data: " + str(e))

    filtered_data = []
    for record in data:
        if start_dt <= datetime.fromisoformat(record['datetime'].replace('Z', '+00:00')) < end_dt:
            filtered_data.append(record)
    if not filtered_data:
        raise ValueError("No data available for the given range")

    total_intensity = sum(record['carbon_intensity'] for record in filtered_data)
    avg_intensity = total_intensity / len(filtered_data)
    return avg_intensity


def get_var(ts_id: str = 'caiso_carbon_intensity', start: str = '', end: str = '') -> float:
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError("Invalid datetime format. Use ISO 8601 format.")

    try:
        data = load_data(f'data/{ts_id}')
    except Exception as e:
        raise RuntimeError("Error loading data: " + str(e))

    filtered_data = []
    for record in data:
        if start_dt <= datetime.fromisoformat(record['datetime'].replace('Z', '+00:00')) < end_dt:
            filtered_data.append(record)
    if not filtered_data:
        raise ValueError("No data available for the given range")

    num_records = len(filtered_data)
    mean_intensity = sum(record['carbon_intensity'] for record in filtered_data) / num_records

    variance = sum((record['carbon_intensity'] - mean_intensity) ** 2 for record in filtered_data) / (num_records - 1)
    
    return variance

def iso_to_datetime(date_str: str) -> Optional[datetime]:
    date_str = date_str.replace('Z', '+00:00')
    dt = datetime.fromisoformat(date_str)
    return dt

def call_api(prompt: str, closest_concept: str, ts_id: str, start_str: str, end_str: str, last_available_date: datetime):
    start_date = datetime.fromisoformat(start_str)
    end_date = datetime.fromisoformat(end_str)
    last_available_date = datetime.fromisoformat(last_available_date)

    if not is_date_range_valid(iso_to_datetime(start_str), iso_to_datetime(end_str), last_available_date):
        closest_concept = 'predict_least_carbon'
        endpoint = "/predict_least_carbon/"
        params = {"ts_id": ts_id}

    if closest_concept == 'maximum_carbon_intensity':
         return f"Calling the function get_max(id, start, end) will return {get_max(ts_id, start_str, end_str)} Tons CO2e/GWh, in 2021."
    elif closest_concept == 'average_carbon_intensity':
        return f"Calling the function get_avg(id, start, end) will return {get_avg(ts_id, start_str, end_str)} Tons CO2e/GWh, on May 2020."
    elif closest_concept == 'minimum_carbon_intensity':
        return f"Calling the function get_min(id, start, end) will return {get_min(ts_id, start_str, end_str)} Tons CO2e/GWh, in 2021."
    elif closest_concept == 'predict_least_carbon':
        return f"Calling the function predict_least_carbon(id, start, end) will return {get_predict_least_carbon(ts_id)['predicted_value']} Tons CO2e/GWh, for the upcoming year."
    else:
        raise ValueError("Unknown concept")

def is_date_range_valid(start_date: Optional[datetime], end_date: Optional[datetime], last_available_date: datetime) -> bool:
    if end_date:
        return end_date <= last_available_date
    return True


def get_prompt_response(prompt: str):
    command = ["python3", "prompt/prompt_processor.py"]

    os.environ['PROMPT_TEXT'] = prompt
    current_directory = os.getcwd()
    process = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, text=True, env=os.environ)
    stdout, stderr = process.communicate()

    stdout_str = stdout.strip()
    print(stdout_str)
    data_tuple = ast.literal_eval(stdout_str)

    start_date_str, end_date_str, concept, last_available_date_str = data_tuple

    output = call_api(prompt, concept, "caiso_carbon_intensity", start_date_str, end_date_str, last_available_date_str)
    
    if process.returncode != 0:
        print(f"Error: Command returned non-zero exit status {result.returncode}")
        return {"error": f"Command failed with exit status {result.returncode}"}
    return output


def get_predict_least_carbon(ts_id: str = 'caiso_carbon_intensity') -> dict:
    yearly_monthly_sums_counts = defaultdict(lambda: defaultdict(lambda: {'sum': 0, 'count': 0}))
    data = load_data(f'data/{ts_id}')
    
    for record in data:
        try:
            date_str = record['datetime'].replace('Z', '+00:00')
            date = datetime.fromisoformat(date_str)
            year = date.year
            month = date.month
            intensity = record['carbon_intensity']
            
            if not isinstance(intensity, (int, float)):
                print(f"Skipping record with non-integer intensity: {record}")
                continue

            yearly_monthly_sums_counts[year][month]['sum'] += intensity
            yearly_monthly_sums_counts[year][month]['count'] += 1
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error processing record {record}: {e}")
            continue

    monthly_averages = defaultdict(list)
    for year, months in yearly_monthly_sums_counts.items():
        for month, values in months.items():
            if values['count'] > 0:
                average = values['sum'] / values['count']
                monthly_averages[month].append(average)

    min_monthly_avg = {}
    for month, averages in monthly_averages.items():
        if averages:
            min_monthly_avg[month] = min(averages)

    predicted_month = min(min_monthly_avg, key=min_monthly_avg.get)
    predicted_value = min_monthly_avg[predicted_month]


    return {
        "year": datetime.now().year + 1,  # Predict for the next year
        "month": predicted_month,
        "predicted_value": round(predicted_value)
    }

def get_predict_advanced_least_carbon(ts_id: str, start_date: str, end_date: str) -> dict:
    def load_data_from_json(ts_id: str):
        with open(f"data/{ts_id}.json", 'r') as file:
            data = json.load(file)
        df = pd.DataFrame(data["data"])
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    def aggregate_monthly(data: pd.DataFrame):
        data.set_index('datetime', inplace=True)
        monthly_data = data.resample('M').mean()  # Use 'M' for monthly frequency
        return monthly_data
    
    def fit_sarima_model(monthly_data: pd.DataFrame):
        model = sm.tsa.SARIMAX(monthly_data, 
                            order=(1, 1, 1), 
                            seasonal_order=(1, 1, 1, 12))
        results = model.fit(disp=False)
        return results
    
    def forecast_future(model_results, periods: int):
        forecast = model_results.get_forecast(steps=periods)
        forecast_df = forecast.summary_frame()
        return forecast_df
    
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError("Invalid date format. Use ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ")

    data = load_data_from_json(ts_id)

    monthly_data = aggregate_monthly(data)

    sarima_fit = fit_sarima_model(monthly_data)

    forecast_periods = pd.date_range(start=start_dt, end=end_dt, freq='M').size
    forecast_df = forecast_future(sarima_fit, forecast_periods)

    forecast_df.index = pd.date_range(start=start_dt, 
                                      periods=forecast_periods, 
                                      freq='M')
    
    forecast_df['month'] = forecast_df.index.month
    monthly_averages = forecast_df.groupby('month')['mean'].mean()
    
    min_month = monthly_averages.idxmin()
    min_month_value = monthly_averages.min()
    
    print("Monthly forecast averages:", monthly_averages.to_dict())
    print(f"Predicted month: {min_month}, Predicted value: {min_month_value}")
    return {
        "month": int(min_month),
        "predicted_value": round(min_month_value) 
    }
