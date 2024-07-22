# Prediction_Services

## Setup

1. **Install Dependencies**

Ensure you have the required Python packages installed by running:
```bash
pip install -r requirements.txt
```

2. **Run the Application**

Start the server with:

```bash
uvicorn app.main:app --reload
```
This will launch a server at http://localhost:8000 with a welcome message.

3. **API Endpoints**

You can access the following endpoints:

    /max/ - Get the maximum value reported in the time series.
    /average/ - Get the average value computed from all the v
time series identified by ts_id.
    /min/ - Get the smallest value reported on the interval
    /variance/ - Get the variance on the interval.
    /preferences/ - Store customer preferences with cust_id and perf.
    /predict_least_carbon/ - Predict the single best month next year during which there will have the lowest average carbon intensity
    /predict_advanced_least_carbon/ - A more rigorous time series analysis of above.
    /give_prompt/ - Submit a prompt to the LLM.
Make sure to provide the correct parameters for each API route.

**Running Tests**
To run the unit tests, use:

```bash
pytest
```
Before running the tests, you may need to set the PYTHONPATH to your current root directory:

```bash
export PYTHONPATH=$(pwd)
```