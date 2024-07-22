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

    /max/ - Description of functionality.
    /average/ - Description of functionality.
    /min/ - Description of functionality.
    /variance/ - Description of functionality.
    /preferences/ - Description of functionality.
    /predict_least_carbon/ - Description of functionality.
    /predict_advanced_least_carbon/ - Description of functionality.
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