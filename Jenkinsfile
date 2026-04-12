pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        GCP_KEY = credentials('gcp-key-secret')
        DB_PASSWORD = "MarwatSecurePass123!" 
        VAULT_TOKEN = "root" 
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Security & Secrets (Vault)') {
            steps {
                script {
                    echo 'Provisioning Secrets in Vault...'
                    // 1. Enable KV engine (ignores error if already enabled)
                    sh "docker exec airflow-vault vault secrets enable -path=airflow kv-v2 || true"
                    
                    // 2. Automatically seed the Postgres Connection URI
                    sh """
                        docker exec airflow-vault vault kv put airflow/connections/postgres_default \
                        conn_uri='postgresql://airflow:airflow@postgres:5432/airflow'
                    """
                    echo '✅ Success: postgres_default connection stored in Vault.'
                }
            }
        }

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    sh 'rm -f ./gcp-key.json' 
                    sh 'mkdir -p ${TF_PLUGIN_CACHE_DIR}'
                    sh 'cp "${GCP_KEY}" ./gcp-key.json'
                    sh 'terraform init -input=false -no-color'
                    sh 'terraform apply -auto-approve -input=false -var="db_password=${DB_PASSWORD}"'
                    sh 'rm -f ./gcp-key.json'
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                sh "rm -f ${DEPLOY_PATH}/config/gcp-key.json"
                sh 'cp "${GCP_KEY}" ' + "${DEPLOY_PATH}/config/gcp-key.json"
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                sleep 15 
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    echo 'Finding Airflow Worker Container...'
                    def worker_id = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()
                    if (worker_id) {
                        sh "docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py"
                    } else {
                        error "FAIL: Airflow Worker container not found."
                    }
                }
            }
        }
    }

    post {
        success { echo ' SUCCESS: Pipeline Completed & Secrets Secured!' }
        failure { echo ' FAILURE: Check logs for permission or Vault errors.' }
    }
}
