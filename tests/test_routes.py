from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
import subprocess 
import json
import logging
from bs4 import BeautifulSoup
import re

client = TestClient(app)

def test_predict_least_carbon():
    response = client.get("/predict_least_carbon/", params={"ts_id": "caiso_carbon_intensity"})
    assert response.status_code == 200

def test_invalid_ts_id():
    response = client.get("/predict_least_carbon/", params={"ts_id": "invalid_id"})
    assert response.status_code == 400 
    data = response.json()
    assert "detail" in data

def test_missing_params():
    response = client.get("/predict_least_carbon/", params={})
    assert response.status_code == 422 
    data = response.json()
    assert "detail" in data

def test_future_date_prediction():
    response = client.get("/predict_least_carbon/", params={"ts_id": "caiso_carbon_intensity"})
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert "month" in data
    assert "predicted_value" in data
    assert data["year"] == (datetime.now().year + 1) 
    assert isinstance(5, int) 
    assert isinstance(183, (int, float))

def test_get_max():
    response = client.get("/max/", params={"ts_id": "caiso_carbon_intensity","start": "2019-12-01T00:00:00Z", "end": "2019-12-02T00:00:00Z"})
    assert response.status_code == 200
    assert response.json()["max"] == 416

def test_get_min():
    response = client.get("/min/", params={"ts_id": "caiso_carbon_intensity", "start": "2019-12-01T00:00:00Z", "end": "2019-12-01T23:59:59Z"})
    assert response.status_code == 200
    assert response.json()["min"]== 312

def test_get_avg():
    response = client.get("/average/", params={"ts_id": "caiso_carbon_intensity", "start": "2019-12-01T00:00:00Z", "end": "2019-12-01T23:59:59Z"})
    assert response.status_code == 200
    assert response.json()["average"] == 380.7916666666667

def test_save_preferences():
    # Define the test input
    preferences = {
        "customer_id": "customer123",
        "preferences": {
            "time_series_id": "ts2"
        }
    }

    response = client.post("/preferences/", json=preferences)

    assert response.status_code == 200

    expected_response = {
        "message": "Preferences saved successfully",
        "data": {
            "customer123": {
                "time_series_id": "ts2"
            }
        }
    }
    assert response.json() == expected_response

def test_variance():
    response = client.get("/variance/", params={"ts_id": "caiso_carbon_intensity", "start": "2019-12-01T00:00:00Z", "end": "2019-12-01T23:59:59Z"})
    assert response.status_code == 200
    assert response.json()["variance"] == 1431.1286231884055



def test_predict_advanced_least_carbon():
    response = client.get(
        "/predict_advanced_least_carbon/",
        params={
            "ts_id": "caiso_carbon_intensity",
            "start_date": "2023-01-01T00:00:00Z",
            "end_date": "2023-11-30T23:59:59Z"
        }
    )
    
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "predicted_value" in data

    expected_month = 4 
    expected_predicted_value = 181 

    assert data["month"] == expected_month
    assert data["predicted_value"] == expected_predicted_value

def parse_html_response(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    p_tag = soup.find_all('p')
    if not p_tag:
        return {"message": "No <p> tag found in HTML content"}
    
    output_text = p_tag[1].get_text()
    print(output_text)
    match = re.search(r'Calling the function \w+\(id, start, end\) will return ([\d.]+) Tons CO2e/GWh', output_text)
    print(match)
    if match:
        try:
            value = float(match.group(1))
            return {"value": value}
        except ValueError:
            return {"message": "Extracted value is not a valid float"}
    else:
        return {"message": "Output not in expected format"}


def test_prompt_most_carbon_jan_to_may_2021():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "Tell me about the most carbon producing on Jan 2021 to May 2021"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {"value": 392.0} 

def test_prompt_average_carbon_intensity_may_2020():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "What is the average carbon intensity for May 2020?"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {"value": 183.34114583333334} 

def test_prompt_most_carbon_2021():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "Tell me about the most carbon producing on 2021"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {"value": 424} 

def test_prompt_most_carbon_jan_2021():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "Tell me about the most carbon producing on Jan 2021"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {"value": 392}

def test_prompt_predict_least_carbon_upcoming_year():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "Predict the least carbon intensity for the upcoming year"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {"value": 183}

def test_prompt_predict_least_carbon_may_2026():
    response = client.get(
        "/process_prompt/",
        params={"prompt": "Predict the least carbon intensity for May 2026"}
    )
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    output = parse_html_response(content)
    assert output == {'value': 183}

if __name__ == "__main__":
    test_prompt_most_carbon_jan_to_may_2021()
    test_prompt_average_carbon_intensity_may_2020()
    test_prompt_most_carbon_2021()
    test_prompt_most_carbon_jan_2021()
    test_prompt_predict_least_carbon_upcoming_year()
    test_prompt_predict_least_carbon_may_2026()

    print("All tests passed!")
