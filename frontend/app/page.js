"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [summary, setSummary] = useState(null);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [anomalyColumn, setAnomalyColumn] = useState("");
  const [anomalies, setAnomalies] = useState(null);
  const [streamedRows, setStreamedRows] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("http://localhost:8000/api/summary")
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Summary API error: ${res.status}`);
          }
          return res.json();
        })
        .then((result) => {
          setSummary(result);

          if (result.numeric_columns?.includes("Data_Value")) {
            setAnomalyColumn("Data_Value");
          } else if (result.numeric_columns?.length > 0) {
            setAnomalyColumn(result.numeric_columns[0]);
          }
        }),

      fetch("http://localhost:8000/api/data?limit=20")
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Data API error: ${res.status}`);
          }
          return res.json();
        })
        .then((result) => {
          setData(result);
        })
    ])
      .catch((error) => {
        console.error("API error:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  function checkAnomalies() {
    if (!anomalyColumn) return;

    setAnomalies(null);

    fetch(
      `http://localhost:8000/api/anomalies?column=${encodeURIComponent(
        anomalyColumn
      )}`
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Anomaly API error: ${res.status}`);
        }

        return res.json();
      })
      .then((result) => {
        setAnomalies(result);
      })
      .catch((error) => {
        console.error("Anomaly error:", error);

        setAnomalies({
          error: "Failed to check anomalies."
        });
      });
  }

  function startStream() {
    setStreamedRows([]);

    const eventSource = new EventSource(
      "http://localhost:8000/api/stream"
    );

    eventSource.onmessage = (event) => {
      try {
        const row = JSON.parse(event.data);

        setStreamedRows((prev) => [
          ...prev,
          row
        ]);
      } catch (error) {
        console.error(
          "Invalid stream data:",
          event.data
        );
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };
  }

  function generateAISummary() {
    setAiSummary(null);
    setAiLoading(true);

    fetch(
      "http://localhost:8000/api/ai-summary?column=Data_Value"
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error(`AI Summary API error: ${res.status}`);
        }

        return res.json();
      })
      .then((result) => {
        setAiSummary(result);
      })
      .catch((error) => {
        console.error("AI summary error:", error);

        setAiSummary({
          error: "Failed to generate AI summary."
        });
      })
      .finally(() => {
        setAiLoading(false);
      });
  }

  if (loading) {
    return (
      <main className="p-8">
        <h1 className="text-2xl font-bold">
          Civic Lite Dashboard
        </h1>

        <p className="mt-4">
          Loading...
        </p>
      </main>
    );
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">
        Civic Lite Dashboard
      </h1>

      {summary ? (
        <div className="mb-6 p-4 bg-gray-100 rounded">
          <p>
            Rows: {summary.row_count}
          </p>

          <p>
            Numeric columns:{" "}
            {summary.numeric_columns?.join(", ") ||
              "None"}
          </p>
        </div>
      ) : (
        <div className="mb-6 p-4 bg-red-100 rounded">
          <p>
            Could not load dataset summary.
          </p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="font-bold mb-2">
          Anomaly Detection
        </h2>

        <select
          value={anomalyColumn}
          onChange={(e) =>
            setAnomalyColumn(e.target.value)
          }
          className="border p-2 mr-2"
        >
          <option value="">
            Select a column
          </option>

          {summary?.numeric_columns?.map((col) => (
            <option
              key={col}
              value={col}
            >
              {col}
            </option>
          ))}
        </select>

        <button
          onClick={checkAnomalies}
          disabled={!anomalyColumn}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
        >
          Check Anomalies
        </button>

        {anomalies && !anomalies.error && (
          <div className="mt-4 p-4 bg-blue-50 rounded">
            <p>
              Found{" "}
              <strong>
                {anomalies.anomaly_count}
              </strong>{" "}
              anomalies in "
              {anomalies.column}".
            </p>

            <p>
              Mean: {anomalies.mean}
            </p>

            <p>
              Standard deviation:{" "}
              {anomalies.standard_deviation}
            </p>
          </div>
        )}

        {anomalies?.error && (
          <p className="mt-2 text-red-600">
            {anomalies.error}
          </p>
        )}
      </div>

      <div className="mb-6">
        <h2 className="font-bold mb-2">
          Live Data Stream
        </h2>

        <button
          onClick={startStream}
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Start Live Stream
        </button>

        <p className="mt-2">
          Streamed rows:{" "}
          {streamedRows.length}
        </p>
      </div>

      <div className="mb-6">
        <h2 className="font-bold mb-2">
          AI Analysis
        </h2>

        <button
          onClick={generateAISummary}
          disabled={aiLoading}
          className="bg-purple-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
        >
          {aiLoading
            ? "Generating..."
            : "Generate AI Summary"}
        </button>

        {aiSummary && (
          <div className="mt-4 p-4 bg-gray-100 rounded">
            <h2 className="font-bold mb-2">
              AI-Generated Summary
            </h2>

            {aiSummary.error ? (
              <p className="text-red-600">
                {aiSummary.error}
              </p>
            ) : (
              <div className="whitespace-pre-wrap">
                {aiSummary.summary ||
                  aiSummary.explanation ||
                  JSON.stringify(aiSummary)}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <h2 className="font-bold mb-2">
          Dataset
        </h2>

        <table className="w-full border-collapse border">
          <thead>
            <tr>
              {data.length > 0 &&
                Object.keys(data[0]).map((col) => (
                  <th
                    key={col}
                    className="border p-2 bg-gray-200 text-left"
                  >
                    {col}
                  </th>
                ))}
            </tr>
          </thead>

          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {Object.values(row).map(
                  (val, j) => (
                    <td
                      key={j}
                      className="border p-2"
                    >
                      {String(val)}
                    </td>
                  )
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}