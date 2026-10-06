# Civic Lite

Civic Lite is a full-stack data analytics dashboard built with **FastAPI and Next.js**. It allows users to explore a civic/public dataset, detect anomalies, stream data in real time, and get AI-generated explanations of the results.

## Features

* View and explore dataset records
* Detect anomalies using Z-scores
* Select different numeric columns for analysis
* Stream dataset records using Server-Sent Events
* Generate AI summaries using Groq
* REST APIs built with FastAPI

## Tech Stack

**Frontend**

* Next.js
* React
* Tailwind CSS

**Backend**

* Python
* FastAPI
* Pandas
* NumPy

**AI**

* Groq API
* `openai/gpt-oss-120b`

## Project Structure

```text
civic-lite/
├── backend/
│   ├── data/
│   │   └── dataset.csv
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   └── ...
│
└── README.md
```

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment and install the dependencies:

```bash
pip install -r requirements.txt
```

Set your Groq API key:

```powershell
$env:GROQ_API_KEY="your_api_key"
```

Start the API:

```bash
python -m uvicorn main:app --reload --port 8000
```

### Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## How It Works

The application reads the dataset through the FastAPI backend. Numeric columns can be analyzed for anomalies using statistical calculations, while the detected results can be passed to Groq to generate a simple explanation.

The dashboard also includes a live data stream using Server-Sent Events.

## Future Improvements

* Add charts and better data visualizations
* Add more filtering options
* Make the anomaly threshold configurable
* Add natural-language dataset queries
* Deploy the application

## Author

**Akshat Chauhan**

[GitHub](https://github.com/Chauhan-Akshat)
