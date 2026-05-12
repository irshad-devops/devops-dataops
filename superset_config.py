import os

# This is the secret key for Superset sessions
SECRET_KEY = os.environ.get("SECRET_KEY", "marwat_secret_77")

# This is the fix! It pulls the correct DB info from Docker
# Fallback is your confirmed Cloud SQL credentials
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_SQLALCHEMY_DATABASE_URI",
    "postgresql+psycopg2://postgres:MarwatSecurePass123!@cloudsql-proxy:5432/flight_analytics"
)

WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False
