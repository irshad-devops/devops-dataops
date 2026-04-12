pipeline {
    agent any
    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        GCP_KEY = credentials('gcp-key-secret')
        DB_PASSWORD = "MarwatSecurePass123!" 
        VAULT_TOKEN = "root" // This must match the token in your docker-compose
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    sh 'rm -f ./gcp-key.json && cp "${GCP_KEY}" ./gcp-key.json'
                    sh 'terraform init -input=false && terraform apply -auto-approve -var="db_password=${DB_PASSWORD}"'
                    sh 'rm -f ./gcp-key.json'
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                sh "cp \"${GCP_KEY}\" ${DEPLOY_PATH}/config/gcp-key.json"
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                // We start the services FIRST
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                echo 'Waiting for Vault and Airflow to be ready...'
                sleep 20 
            }
        }

        stage('Security & Secrets (Vault)') {
            steps {
                script {
                    echo 'Provisioning Secrets in Vault...'
                    // We must pass VAULT_TOKEN and VAULT_ADDR into the docker exec environment
                    sh """
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault secrets enable -path=airflow kv-v2 || true
                        
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault kv put airflow/connections/postgres_default \
                        conn_uri='postgresql://airflow:airflow@postgres:5432/airflow'
                    """
                    echo '✅ Success: Secrets injected into Vault.'
                }
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    def worker_id = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()
                    if (worker_id) {
                        sh "docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py"
                    }
                }
            }
        }
    }

    post {
        success { echo '✅ SUCCESS: Pipeline Completed!' }
        failure { echo '❌ FAILURE: Check Vault logs or container status.' }
    }
}
