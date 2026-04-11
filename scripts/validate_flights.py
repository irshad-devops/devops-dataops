import pandas as pd
import sys
import os

def validate():
    print("🚀 Starting Production DataOps Quality Gate (Great Expectations)...")
    
    file_path = '/opt/airflow/dags/data.csv'
    
    # 1. Verify file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: Data file not found at {file_path}")
        sys.exit(1)

    try:
        # 2. Import Great Expectations
        import great_expectations as gx
        
        # 3. Create a temporary (ephemeral) Data Context
        context = gx.get_context()
        
        # 4. Read the data
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip() # Clean column names

        # 5. Connect GX to the Pandas DataFrame
        datasource_name = "flight_datasource"
        data_asset_name = "flight_asset"
        
        datasource = context.sources.add_pandas(name=datasource_name)
        asset = datasource.add_dataframe_asset(name=data_asset_name)
        
        # Create a validator
        validator = asset.get_validator(batch_request=asset.build_batch_request(dataframe=df))

        print("🔍 Running Schema and Data Quality Expectations...")

        # --- EXPECTATION SUITE ---
        
        # Check A: Required columns exist
        validator.expect_column_to_exist("DEST_COUNTRY_NAME")
        validator.expect_column_to_exist("count")

        # Check B: Data Quality (No Nulls)
        validator.expect_column_values_to_not_be_null("DEST_COUNTRY_NAME")
        
        # Check C: Logic Check (Count must be non-negative)
        validator.expect_column_values_to_be_between("count", min_value=0)

        # Check D: Value constraints (Example: Ensure counts are integers)
        validator.expect_column_values_to_be_of_type("count", "int64")

        # 6. Execute Validation
        validation_result = validator.validate()

        if validation_result["success"]:
            print(f"✅ SUCCESS: Great Expectations Validation Passed! {len(df)} rows verified.")
            sys.exit(0)
        else:
            print("❌ FAILURE: Data Quality Gate Failed! Check detailed results:")
            for result in validation_result["results"]:
                if not result["exception_info"]["raised_exception"] and not result["success"]:
                    print(f"  - Failed Expectation: {result['expectation_config']['expectation_type']}")
            sys.exit(1)

    except ImportError:
        print("❌ Critical Error: 'great_expectations' library not found! Ensure Docker image was rebuilt.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ System Error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate()
