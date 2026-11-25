from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import io
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hisaab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_file = None


@app.get("/")
def home():
    return {
        "message": "Hisaab backend is running!"
    }


# Find the latest uploaded/cleaned file
def get_current_file():

    global current_file

    # If current_file is already available
    if current_file is not None and os.path.exists(current_file):
        return current_file

    # Look for cleaned files first
    processed_folder = "data/processed"

    if os.path.exists(processed_folder):

        cleaned_files = [
            os.path.join(processed_folder, file)
            for file in os.listdir(processed_folder)
            if file.endswith(".csv")
        ]

        if cleaned_files:
            latest_file = max(
                cleaned_files,
                key=os.path.getmtime
            )

            current_file = latest_file

            return current_file

    # If no cleaned file exists, look for raw files
    raw_folder = "data/raw"

    if os.path.exists(raw_folder):

        raw_files = [
            os.path.join(raw_folder, file)
            for file in os.listdir(raw_folder)
            if file.endswith(".csv")
            or file.endswith(".xlsx")
        ]

        if raw_files:
            latest_file = max(
                raw_files,
                key=os.path.getmtime
            )

            current_file = latest_file

            return current_file

    return None


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    global current_file

    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(
            io.BytesIO(contents)
        )

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(
            io.BytesIO(contents)
        )

    else:
        return {
            "error": "Only CSV and Excel files are allowed."
        }

    save_path = os.path.join(
        "data",
        "raw",
        file.filename
    )

    current_file = save_path

    with open(save_path, "wb") as f:
        f.write(contents)

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "saved_to": save_path
    }


@app.get("/check-data")
def check_data():

    file_path = "data/raw/test_sales.csv"

    df = pd.read_csv(file_path)

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
        "data_types": df.dtypes.astype(str).to_dict()
    }


@app.get("/clean-data")
def clean_data():

    global current_file

    current_file = get_current_file()

    if current_file is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current_file.endswith(".csv"):
        df = pd.read_csv(current_file)

    else:
        df = pd.read_excel(current_file)

    original_rows = len(df)

    # Count duplicate rows before cleaning
    duplicates_removed = int(
        df.duplicated().sum()
    )

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Convert Date column into proper date format
    invalid_dates = 0

    if "Date" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        invalid_dates = int(
            df["Date"].isnull().sum()
        )

    # Fill missing numeric values with 0
    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    for column in numeric_columns:

        df[column] = df[column].fillna(0)

    # Fill missing text values with Unknown
    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        df[column] = df[column].fillna(
            "Unknown"
        )

    # Create cleaned file name
    filename = os.path.basename(
        current_file
    )

    name, extension = os.path.splitext(
        filename
    )

    # Prevent cleaned_cleaned_filename
    if name.startswith("cleaned_"):

        name = name.replace(
            "cleaned_",
            "",
            1
        )

    output_file = os.path.join(
        "data",
        "processed",
        "cleaned_" + name + ".csv"
    )

    # Save cleaned dataset
    df.to_csv(
        output_file,
        index=False
    )

    # Make cleaned file the current dataset
    current_file = output_file

    return {
        "message": "Data cleaned successfully!",
        "original_rows": original_rows,
        "rows_after_cleaning": len(df),
        "duplicates_removed": duplicates_removed,
        "invalid_dates": invalid_dates,
        "missing_values_remaining": int(
            df.isnull().sum().sum()
        ),
        "saved_to": output_file
    }


@app.get("/download-cleaned-data")
def download_cleaned_data():

    current = get_current_file()

    if current is None:
        return {
            "error": "No cleaned file is available."
        }

    # Make sure it is actually a cleaned file
    if "processed" not in current:
        return {
            "error": "Please clean the data first."
        }

    if not os.path.exists(current):
        return {
            "error": "Cleaned file not found."
        }

    return FileResponse(
        path=current,
        filename="cleaned_data.csv",
        media_type="text/csv"
    )


@app.get("/summary")
def dataset_summary():

    current = get_current_file()

    if current is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current.endswith(".csv"):
        df = pd.read_csv(current)

    else:
        df = pd.read_excel(current)

    summary = {}

    for column in df.columns:

        summary[column] = {
            "data_type": str(
                df[column].dtype
            ),
            "missing_values": int(
                df[column].isnull().sum()
            ),
            "unique_values": int(
                df[column].nunique()
            )
        }

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "summary": summary
    }


@app.get("/analytics")
def analytics():

    current = get_current_file()

    if current is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current.endswith(".csv"):
        df = pd.read_csv(current)

    else:
        df = pd.read_excel(current)

    total_quantity = 0
    total_sales = 0
    average_price = 0
    best_product = None

    if "Quantity" in df.columns:

        total_quantity = int(
            df["Quantity"].sum()
        )

    if (
        "Price" in df.columns
        and "Quantity" in df.columns
    ):

        total_sales = float(
            (
                df["Price"]
                * df["Quantity"]
            ).sum()
        )

    if "Price" in df.columns:

        average_price = float(
            df["Price"].mean()
        )

    if (
        "Product" in df.columns
        and "Quantity" in df.columns
    ):

        product_sales = (
            df.groupby("Product")[
                "Quantity"
            ].sum()
        )

        best_product = (
            product_sales.idxmax()
        )

    return {
        "total_quantity": total_quantity,
        "total_sales": total_sales,
        "average_price": average_price,
        "best_selling_product": best_product
    }


@app.get("/charts")
def chart_data():

    current = get_current_file()

    if current is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current.endswith(".csv"):
        df = pd.read_csv(current)

    else:
        df = pd.read_excel(current)

    result = {}

    # Sales by product
    if (
        "Product" in df.columns
        and "Quantity" in df.columns
        and "Price" in df.columns
    ):

        product_sales = (
            df.assign(
                Sales=(
                    df["Quantity"]
                    * df["Price"]
                )
            )
            .groupby("Product")[
                "Sales"
            ]
            .sum()
        )

        result["sales_by_product"] = (
            product_sales.to_dict()
        )

    # Quantity by product
    if (
        "Product" in df.columns
        and "Quantity" in df.columns
    ):

        quantity_by_product = (
            df.groupby("Product")[
                "Quantity"
            ]
            .sum()
        )

        result["quantity_by_product"] = (
            quantity_by_product.to_dict()
        )

    # Sales over time
    if (
        "Date" in df.columns
        and "Quantity" in df.columns
        and "Price" in df.columns
    ):

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        df["Sales"] = (
            df["Quantity"]
            * df["Price"]
        )

        sales_over_time = (
            df.dropna(
                subset=["Date"]
            )
            .groupby("Date")[
                "Sales"
            ]
            .sum()
        )

        result["sales_over_time"] = {

            str(date.date()):
            float(sales)

            for date, sales
            in sales_over_time.items()
        }

    return result


@app.get("/preview")
def preview_data():

    current = get_current_file()

    if current is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current.endswith(".csv"):
        df = pd.read_csv(current)

    else:
        df = pd.read_excel(current)

    return {
        "columns": list(
            df.columns
        ),

        "rows": (
            df.head(5)
            .fillna("")
            .to_dict(
                orient="records"
            )
        )
    }


@app.get("/data-quality")
def data_quality():

    current = get_current_file()

    if current is None:
        return {
            "error": "No file has been uploaded yet."
        }

    if current.endswith(".csv"):
        df = pd.read_csv(current)

    else:
        df = pd.read_excel(current)

    return {
        "total_rows": len(df),

        "total_columns": len(
            df.columns
        ),

        "missing_values": int(
            df.isnull()
            .sum()
            .sum()
        ),

        "duplicate_rows": int(
            df.duplicated()
            .sum()
        ),

        "missing_by_column": (
            df.isnull()
            .sum()
            .to_dict()
        ),

        "data_types": (
            df.dtypes
            .astype(str)
            .to_dict()
        )
    }