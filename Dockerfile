# ---- Base image ----
FROM python:3.11-slim

# ---- Working directory ----
WORKDIR /app

# ---- Install dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy source code ----
COPY . .

# ---- Expose FastAPI port ----
EXPOSE 8000

# ---- Start the app ----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
