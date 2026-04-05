import pandas as pd
import sys

def validate():
    print("🚀 Starting Data Quality Validation (Airflow Quality Gate)...")
    
    # 1. Load the data
    try:
        df = pd.read_csv("/opt/airflow/dags/data.csv")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)
    
    # 2. Define Quality Rules (Your "Expectations")
    print("🔍 Checking column structure and business rules...")
    
    errors = []

    # Rule 1: Schema Check
    required_columns = ["count", "DEST_COUNTRY_NAME"]
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")

    # Rule 2: Business Logic Check (No negative flights)
    if "count" in df.columns:
        negative_counts = df[df["count"] < 0]
        if not negative_counts.empty:
            errors.append(f"Found {len(negative_counts)} rows with negative flight counts")

    # 3. Final Decision Logic
    if not errors:
        print("✅ DATA QUALITY PASSED!")
        # For your interview: This exit(0) signals Airflow to move to the Security task
        sys.exit(0)
    else:
        print("🛑 DATA QUALITY FAILED!")
        for err in errors:
            print(f"   - {err}")
        # This exit(1) acts as the Circuit Breaker to stop the pipeline
        sys.exit(1)

if __name__ == "__main__":
    validate()
