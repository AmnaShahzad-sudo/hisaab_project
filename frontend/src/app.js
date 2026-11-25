import React, { useEffect, useState } from "react";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from "chart.js";

import { Bar, Doughnut, Line } from "react-chartjs-2";
import "./App.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

function App() {
  const [analytics, setAnalytics] = useState(null);
  const [charts, setCharts] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dataQuality, setDataQuality] = useState(null);
  const [cleaningResult, setCleaningResult] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");

  // Refresh dashboard data
  const refreshDashboard = async () => {
    try {
      const analyticsResponse = await fetch(
        "http://127.0.0.1:8000/analytics"
      );
      const analyticsData = await analyticsResponse.json();
      setAnalytics(analyticsData);

      const chartsResponse = await fetch(
        "http://127.0.0.1:8000/charts"
      );
      const chartsData = await chartsResponse.json();
      setCharts(chartsData);

      const previewResponse = await fetch(
        "http://127.0.0.1:8000/preview"
      );
      const previewData = await previewResponse.json();
      setPreview(previewData);

      const qualityResponse = await fetch(
        "http://127.0.0.1:8000/data-quality"
      );
      const qualityData = await qualityResponse.json();
      setDataQuality(qualityData);

    } catch (error) {
      console.log("Dashboard refresh error:", error);
    }
  };

  // Upload file function
  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok || data.error) {
        setMessage(data.error || "Upload failed.");
        return;
      }

      setMessage("File uploaded successfully!");

      window.location.reload();

    } catch (error) {
      setMessage("Upload failed. Please try again.");
    }
  };

  // Clean data function
  const handleCleanData = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/clean-data"
      );

      const data = await response.json();

      if (data.error) {
        setMessage(data.error);
        return;
      }

      // Store cleaning result
      setCleaningResult(data);

      setMessage("Data cleaned successfully!");

      // Refresh dashboard with cleaned data
      await refreshDashboard();

    } catch (error) {
      setMessage("Data cleaning failed. Please try again.");
    }
  };

  // Download cleaned data function
  const handleDownload = () => {
    window.open(
      "http://127.0.0.1:8000/download-cleaned-data",
      "_blank"
    );
  };

  // Fetch backend data when dashboard first loads
  useEffect(() => {
    refreshDashboard();
  }, []);

  // Loading screen
  if (
    !analytics ||
    !charts ||
    !preview ||
    !dataQuality
  ) {
    return <h2>Loading Hisaab Dashboard...</h2>;
  }

  // Error screen
  if (
    analytics.error ||
    charts.error ||
    preview.error ||
    dataQuality.error
  ) {
    return (
      <h2>
        {analytics.error ||
          charts.error ||
          preview.error ||
          dataQuality.error}
      </h2>
    );
  }

  // Sales by product chart
  const salesData = {
    labels: Object.keys(
      charts.sales_by_product || {}
    ),

    datasets: [
      {
        label: "Sales (Rs.)",

        data: Object.values(
          charts.sales_by_product || {}
        ),

        backgroundColor: "#6558d3",
      },
    ],
  };

  // Quantity by product chart
  const quantityData = {
    labels: Object.keys(
      charts.quantity_by_product || {}
    ),

    datasets: [
      {
        label: "Quantity",

        data: Object.values(
          charts.quantity_by_product || {}
        ),

        backgroundColor: [
          "#6558d3",
          "#39a9a5",
          "#f4a261",
        ],
      },
    ],
  };

  // Sales over time chart
  const dates = Object.keys(
    charts.sales_over_time || {}
  );

  const timeData = {
    labels: dates,

    datasets: [
      {
        label: "Daily Sales (Rs.)",

        data: dates.map(
          (date) =>
            charts.sales_over_time[date]
        ),

        borderColor: "#6558d3",
        backgroundColor: "#6558d3",
        tension: 0.3,
      },
    ],
  };

  return (
    <div className="dashboard">

      {/* Header */}
      <header>
        <h1>Hisaab</h1>

        <p>
          AI-Powered Business Intelligence Copilot
        </p>
      </header>


      {/* File Upload Section */}
      <div className="upload-section">

        <h2>Upload Your Business Data</h2>

        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(e) =>
            setSelectedFile(
              e.target.files[0]
            )
          }
        />

        <button onClick={handleUpload}>
          Upload File
        </button>

        <button onClick={handleCleanData}>
          Clean My Data
        </button>

        <button onClick={handleDownload}>
          Download Cleaned Data
        </button>

        <p>{message}</p>

      </div>


      {/* Business Overview */}
      <h2>Business Overview</h2>

      <div className="cards">

        <div className="card">

          <h3>Total Sales</h3>

          <h2>
            Rs.{" "}
            {analytics.total_sales.toLocaleString()}
          </h2>

        </div>


        <div className="card">

          <h3>Total Quantity</h3>

          <h2>
            {analytics.total_quantity}
          </h2>

        </div>


        <div className="card">

          <h3>Average Price</h3>

          <h2>
            Rs.{" "}
            {analytics.average_price.toLocaleString()}
          </h2>

        </div>


        <div className="card">

          <h3>Best Selling Product</h3>

          <h2>
            {analytics.best_selling_product}
          </h2>

        </div>

      </div>


      {/* Data Quality Report */}
      <div className="section">

        <h2>Data Quality Report</h2>

        <div className="cards">

          <div className="card">

            <h3>Total Rows</h3>

            <p>
              {dataQuality.total_rows}
            </p>

          </div>


          <div className="card">

            <h3>Total Columns</h3>

            <p>
              {dataQuality.total_columns}
            </p>

          </div>


          <div className="card">

            <h3>Missing Values</h3>

            <p>
              {dataQuality.missing_values}
            </p>

          </div>


          <div className="card">

            <h3>Duplicate Rows</h3>

            <p>
              {dataQuality.duplicate_rows}
            </p>

          </div>

        </div>

      </div>


      {/* Cleaning Result */}
      {cleaningResult && (
        <div className="section">

          <h2>Cleaning Result</h2>

          <div className="cards">

            <div className="card">

              <h3>Original Rows</h3>

              <p>
                {cleaningResult.original_rows}
              </p>

            </div>


            <div className="card">

              <h3>Rows After Cleaning</h3>

              <p>
                {cleaningResult.rows_after_cleaning}
              </p>

            </div>


            <div className="card">

              <h3>Duplicates Removed</h3>

              <p>
                {cleaningResult.duplicates_removed}
              </p>

            </div>


            <div className="card">

              <h3>Missing Values Remaining</h3>

              <p>
                {cleaningResult.missing_values_remaining}
              </p>

            </div>

          </div>

        </div>
      )}


      {/* Uploaded Data Preview */}
      <h2>Uploaded Data Preview</h2>

      <div className="preview-table">

        <table>

          <thead>

            <tr>

              {preview.columns.map(
                (column) => (
                  <th key={column}>
                    {column}
                  </th>
                )
              )}

            </tr>

          </thead>


          <tbody>

            {preview.rows.map(
              (row, index) => (

                <tr key={index}>

                  {preview.columns.map(
                    (column) => (

                      <td key={column}>
                        {row[column]}
                      </td>

                    )
                  )}

                </tr>

              )
            )}

          </tbody>

        </table>

      </div>


      {/* Sales Analytics */}
      <h2>Sales Analytics</h2>

      <div className="charts">

        <div className="chart-card">

          <h3>
            Sales by Product
          </h3>

          <Bar data={salesData} />

        </div>


        <div className="chart-card">

          <h3>
            Quantity by Product
          </h3>

          <Doughnut
            data={quantityData}
          />

        </div>


        <div className="chart-card">

          <h3>
            Sales Over Time
          </h3>

          <Line data={timeData} />

        </div>

      </div>

    </div>
  );
}

export default App;