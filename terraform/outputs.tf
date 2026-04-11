output "bucket_name" {
  value = google_storage_bucket.data_lake.name
}

output "data_path" {
  value = "gs://${google_storage_bucket.data_lake.name}/raw/data.csv"
}

output "db_instance_connection" {
  value = google_sql_database_instance.flight_db.connection_name
}

