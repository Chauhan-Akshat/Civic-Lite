from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
app = FastAPI(title="Civic Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "dataset.csv"

def load_data():
    return pd.read_csv(DATA_PATH)

@app.get("/")
def root():
    return {"message": "Civic Lite API running"}

@app.get("/api/data")
def get_data(limit: int = 20):
    limit = max(1, min(limit, 1000))
    df = pd.read_csv(DATA_PATH, nrows=limit)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict(orient="records")

@app.get("/api/anomalies")
def get_anomalies(column: str = "Data_Value"):
    df = load_data()

    if column not in df.columns:
        return {
            "error": f"Column '{column}' not found",
            "available_columns": df.columns.tolist()
        }

    if column not in df.select_dtypes(include=[np.number]).columns:
        return {"error": f"Column '{column}' must be numeric"}

    df = df.dropna(subset=[column]).copy()
    mean = df[column].mean()
    std = df[column].std()

    if std == 0 or pd.isna(std):
        anomalies = df.iloc[0:0].copy()
    else:
        df["z_score"] = (df[column] - mean) / std
        anomalies = df[df["z_score"].abs() > 3].copy()

    anomalies = anomalies.replace([np.inf, -np.inf], np.nan)
    anomalies = anomalies.astype(object).where(pd.notna(anomalies), None)

    return {
        "column": column,
        "mean": None if pd.isna(mean) else float(mean),
        "standard_deviation": None if pd.isna(std) else float(std),
        "anomaly_count": int(len(anomalies)),
        "anomalies": anomalies.to_dict(orient="records")
    }

@app.get("/api/summary")
def get_summary():
    df = pd.read_csv(DATA_PATH)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    return {
        "row_count": int(len(df)),
        "numeric_columns": numeric_columns
    }
import asyncio
import json
from fastapi.responses import StreamingResponse

@app.get("/api/stream")
async def stream_data():
    df = pd.read_csv(DATA_PATH)

    async def generate():
        for _, row in df.iterrows():
            record = row.replace([np.inf, -np.inf], np.nan)
            record = record.where(pd.notna(record), None)
            record = record.to_dict()

            yield f"data: {json.dumps(record, allow_nan=False)}\n\n"

            await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.get("/api/ai-summary")
def ai_summary(column: str, threshold: float = 2.0):
    df = load_data()
    result = detect_anomalies(df, column, threshold)

    prompt = f"""
You are analyzing a public dataset for anomalies.
Column: {column}
Mean: {result['mean']}, Std Dev: {result['std_dev']}
Number of anomalies found: {result['anomaly_count']}
Sample anomalies: {result['anomalies'][:3]}

Write a 2-3 sentence plain-English summary of what this means for someone
who is not a data analyst.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    return {"summary": response.choices[0].message.content}