import great_expectations as gx
import pandas as pd
import sys
import time

def run_validation():
    print("🚀 Starting Production DataOps Quality Gate (GX 1.0 Stable API)...")
    
    try:
        # 1. Initialize Context
        context = gx.get_context()

        # 2. Load the Data
        csv_path = "/opt/airflow/dags/data.csv"
        df = pd.read_csv(csv_path)
        
        # 3. Create or Get Expectation Suite
        suite_name = "flight_quality_suite"
        try:
            # If suite exists, we delete and recreate to ensure rules are updated
            context.suites.delete(name=suite_name)
        except Exception:
            pass
            
        suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
        
        # --- MATCHING YOUR ACTUAL CSV COLUMNS ---
        # Rule 1: DEST_COUNTRY_NAME should not be null
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="DEST_COUNTRY_NAME"))
        
        # Rule 2: count should be 0 or higher
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="count", min_value=0))

        # 4. Setup Data Infrastructure (Fluent API)
        # Use a unique datasource name to avoid metadata collisions
        ds_name = f"ds_flights_{int(time.time())}" 
        ds = context.data_sources.add_pandas(name=ds_name)
        asset = ds.add_dataframe_asset(name="flight_asset")
        
        # Define how to handle the data batch
        batch_definition = asset.add_batch_definition_whole_dataframe(name="batch_def")

        # 5. Create a Validation Definition
        validation_def = gx.ValidationDefinition(
            name=f"val_def_{int(time.time())}",
            data=batch_definition,
            suite=suite
        )

        # 6. Run Validation
        print("🔍 Running Data Quality checks on columns: DEST_COUNTRY_NAME, count...")
        results = validation_def.run(batch_parameters={"dataframe": df})
        
        if results.success:
            print("✅ Data Quality Gate Passed! Columns matched and data is valid.")
            sys.exit(0)
        else:
            print("❌ Data Quality Gate Failed!")
            print(f"Stats: {results.statistics}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ System Error: {str(e)}")
        # FINAL SAFETY NET: Manual pandas check using the CORRECT columns
        print("🔄 Performing Manual Data Integrity Check...")
        try:
            if df['DEST_COUNTRY_NAME'].notnull().all() and (df['count'] >= 0).all():
                 print("✅ Manual Integrity Check Passed. Moving Forward.")
                 sys.exit(0)
            else:
                 print("❌ Manual Integrity Check Failed.")
                 sys.exit(1)
        except KeyError as name_error:
            print(f"❌ Column Name Error: {str(name_error)}. Please check CSV headers.")
            sys.exit(1)

if __name__ == "__main__":
    run_validation()
