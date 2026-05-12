pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        GCP_KEY = credentials('gcp-key-secret')
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Terraform (GCP Infra)') {
            steps {
                dir('terraform') {

                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASS')
                    ]) {

                        sh '''
                        cp "${GCP_KEY}" ./gcp-key.json

                        terraform init -input=false

                        terraform apply -auto-approve \
                          -var="db_password=${DB_PASS}"

                        rm -f ./gcp-key.json
                        '''
                    }
                }
            }
        }

        stage('Prepare Environment') {

            steps {

                withCredentials([
                    string(credentialsId: 'db-password', variable: 'DB_PASS'),
                    string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN')
                ]) {

                    sh """
                    mkdir -p ${DEPLOY_PATH}/config

                    # Copy GCP Service Account Key
                    cp ${GCP_KEY} ${DEPLOY_PATH}/config/gcp-key.json

                    # Secure permissions
                    chmod 600 ${DEPLOY_PATH}/config/gcp-key.json

                    # Create secure .env file
                    cat <<EOF > ${DEPLOY_PATH}/.env
AIRFLOW_DB_CONN=postgresql+psycopg2://postgres:${DB_PASS}@cloudsql-proxy:5432/flight_analytics

AIRFLOW_RESULT_BACKEND=db+postgresql://postgres:${DB_PASS}@cloudsql-proxy:5432/flight_analytics

SUPERSET_DB_CONN=postgresql+psycopg2://postgres:${DB_PASS}@cloudsql-proxy:5432/superset_db

VAULT_TOKEN=${VAULT_TOKEN}
EOF

                    chmod 600 ${DEPLOY_PATH}/.env
                    """
                }
            }
        }

        stage('Deploy Docker Stack') {

            steps {

                sh """
                cd ${DEPLOY_PATH}

                docker compose down -v

                docker compose up -d --build
                """

                sleep 40
            }
        }

        stage('Inject Secrets into Vault') {

            steps {

                withCredentials([
                    string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN'),
                    string(credentialsId: 'db-password', variable: 'DB_PASS')
                ]) {

                    sh '''
                    docker exec airflow-vault sh -c "
                    export VAULT_ADDR=http://127.0.0.1:8200
                    export VAULT_TOKEN=${VAULT_TOKEN}

                    vault secrets enable -path=airflow kv-v2 || true

                    vault kv put airflow/connections/postgres_default \
                    conn_uri='postgresql://postgres:${DB_PASS}@cloudsql-proxy:5432/flight_analytics'
                    "
                    '''
                }
            }
        }

        stage('Verify Airflow Containers') {

            steps {

                sh '''
                docker ps | grep airflow
                '''
            }
        }

        stage('Data Quality Check') {

            steps {

                script {

                    def worker = sh(
                        script: "docker ps -qf 'name=airflow-worker' | head -n 1",
                        returnStdout: true
                    ).trim()

                    if (worker) {

                        sh """
                        docker exec ${worker} \
                        python3 /opt/airflow/scripts/validate_flights.py
                        """

                    } else {

                        error "Airflow worker not running"
                    }
                }
            }
        }
    }

    post {

        success {

            echo '🚀 SUCCESS: Full pipeline completed securely'
        }

        failure {

            echo '❌ FAILURE: Check Jenkins logs'
        }

        always {

            sh '''
            rm -f ${DEPLOY_PATH}/terraform/gcp-key.json || true
            '''
        }
    }
}
