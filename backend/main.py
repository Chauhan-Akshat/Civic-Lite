from pathlib import Path
import os
import json
import asyncio

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq

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


def detect_anomalies(df, column, threshold=2.0):
    if column not in df.columns:
        return {
            "error": f"Column '{column}' not found",
            "anomaly_count": 0,
            "anomalies": []
        }

    if column not in df.select_dtypes(include=[np.number]).columns:
        return {
            "error": f"Column '{column}' must be numeric",
            "anomaly_count": 0,
            "anomalies": []
        }

    df = df.dropna(subset=[column]).copy()

    mean = df[column].mean()
    std = df[column].std()

    if std == 0 or pd.isna(std):
        anomalies = df.iloc[0:0].copy()
    else:
        df["z_score"] = (df[column] - mean) / std
        anomalies = df[df["z_score"].abs() > threshold].copy()

    anomalies = anomalies.replace([np.inf, -np.inf], np.nan)
    anomalies = anomalies.astype(object).where(pd.notna(anomalies), None)

    return {
        "column": column,
        "mean": None if pd.isna(mean) else float(mean),
        "standard_deviation": None if pd.isna(std) else float(std),
        "anomaly_count": int(len(anomalies)),
        "anomalies": anomalies.to_dict(orient="records")
    }


@app.get("/api/anomalies")
def get_anomalies(column: str = "Data_Value"):
    df = load_data()
    return detect_anomalies(df, column, 3.0)


@app.get("/api/summary")
def get_summary():
    df = pd.read_csv(DATA_PATH)

    numeric_columns = df.select_dtypes(
        include=[np.number]
    ).columns.tolist()

    return {
        "row_count": int(len(df)),
        "numeric_columns": numeric_columns
    }


@app.get("/api/stream")
async def stream_data():
    df = pd.read_csv(DATA_PATH)

    async def generate():
        for _, row in df.iterrows():
            record = row.to_dict()

            cleaned_record = {}

            for key, value in record.items():
                if pd.isna(value) or value in [np.inf, -np.inf]:
                    cleaned_record[key] = None
                elif isinstance(value, np.generic):
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value

            yield f"data: {json.dumps(cleaned_record, allow_nan=False)}\n\n"

            await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


groq_api_key = os.getenv("GROQ_API_KEY")

if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)
else:
    groq_client = None


@app.get("/api/ai-summary")
def ai_summary(column: str, threshold: float = 2.0):
    if groq_client is None:
        return {
            "error": "GROQ_API_KEY is not set."
        }

    df = load_data()

    result = detect_anomalies(
        df,
        column,
        threshold
    )

    if "error" in result:
        return result

    prompt = f"""
You are analyzing a public dataset for anomalies.

Dataset column analyzed: {result["column"]}
Mean: {result["mean"]}
Standard deviation: {result["standard_deviation"]}
Number of anomalies found: {result["anomaly_count"]}

Sample anomalies:
{result["anomalies"][:3]}

Explain these findings in simple, plain English.

Mention:
1. What the analyzed column represents if it can be inferred.
2. What the mean and standard deviation tell us.
3. What the anomalies mean.
4. Any useful pattern visible in the sample anomalies.

Keep the explanation concise and understandable for a general user.
"""

    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analysis assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=500
        )

        summary = response.choices[0].message.content

        return {
            "column": column,
            "threshold": threshold,
            "anomaly_count": result["anomaly_count"],
            "summary": summary
        }

    except Exception as e:
        return {
            "error": f"AI summary failed: {str(e)}"
        }