from fastapi import APIRouter, HTTPException, Query, FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List,Optional
from app.models import CarbonIntensityRecord, Preferences
from app.services import get_max, get_min, get_avg, get_var, get_predict_least_carbon, save_customer_preferences, get_prompt_response, get_predict_advanced_least_carbon
from collections import defaultdict
import json
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/max/")
def max_value(ts_id: str, start: str, end: str):
    try:
        return {"max": get_max(ts_id, start, end)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/min/")
def min_value(ts_id: str, start: str, end: str):
    try:
        return {"min": get_min(ts_id, start, end)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/predict_least_carbon/")
def predict_least_carbon(ts_id: str) -> dict:
    try:
        print("hello")
        prediction = get_predict_least_carbon(ts_id)
        return {
            "year": prediction["year"],
            "month": prediction["month"],
            "predicted_value": prediction["predicted_value"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/predict_advanced_least_carbon/")
def predict_advanced_least_carbon(ts_id: str, start_date: str, end_date: str) -> dict:
    try:
        prediction = get_predict_advanced_least_carbon(ts_id, start_date, end_date)
        return {
            "month": prediction["month"],
            "predicted_value": prediction["predicted_value"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/preferences/")
def save_preferences(preferences: Preferences):
    try:
        result = save_customer_preferences(preferences.customer_id, preferences.preferences)
        return {"message": "Preferences saved successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/average/")
def average(ts_id: str, start: str, end: str):
    try:
        avg = get_avg(ts_id, start, end)
        return {"average": avg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/variance/")
def variance(ts_id: str, start: str, end: str):
    try:
        var = get_var(ts_id, start, end)
        return {"variance": var}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/give_prompt/", response_class=HTMLResponse)
async def give_prompt(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@router.get("/process_prompt/", response_class=HTMLResponse)
async def process_prompt(request: Request, prompt: str):
    output = get_prompt_response(prompt)
    return templates.TemplateResponse("form.html", {"request": request, "input": prompt, "output": output})