FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV NAME World

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
