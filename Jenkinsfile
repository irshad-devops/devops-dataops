pipeline {
    agent any

    environment {
        // Absolute path to your Airflow project directory
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

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    script {
                        echo 'Checking Cloud Infrastructure...'
                        sh 'rm -f ./gcp-key.json && cp "${GCP_KEY}" ./gcp-key.json'
                        
                        // Retry logic handles the intermittent DNS timeouts
                        retry(2) {
                            sh 'terraform init -input=false -no-color'
                            sh 'terraform apply -auto-approve -input=false -var="db_password=${DB_PASSWORD}"'
                        }
                        sh 'rm -f ./gcp-key.json'
                    }
                }
            }
        }

        stage('Deploy & Fix Permissions') {
            steps {
                script {
                    echo 'Syncing files to local deployment path...'
                    // Requires the visudo change mentioned above
                    sh """
                        sudo mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/
                        sudo chown -R jenkins:jenkins ${DEPLOY_PATH}
                        cp -r dags/* ${DEPLOY_PATH}/dags/
                        cp -r scripts/* ${DEPLOY_PATH}/scripts/
                        rm -f ${DEPLOY_PATH}/config/gcp-key.json
                        cp "${GCP_KEY}" ${DEPLOY_PATH}/config/gcp-key.json
                    """
                }
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                echo 'Starting Docker containers...'
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                echo 'Waiting 20s for Vault and DB initialization...'
                sleep 20 
            }
        }

        stage('Security & Secrets (Vault)') {
            steps {
                script {
                    echo 'Injecting Airflow secrets into Vault...'
                    // We explicitly pass VAULT_TOKEN to the container environment
                    sh """
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault secrets enable -path=airflow kv-v2 || true
                        
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault kv put airflow/connections/postgres_default \
                        conn_uri='postgresql://airflow:airflow@postgres:5432/airflow'
                    """
                }
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    echo 'Running data validation checks...'
                    def worker_id = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()
                    if (worker_id) {
                        sh "docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py"
                    } else {
                        error "Airflow worker not found. Deployment might have failed."
                    }
                }
            }
        }
    }

    post {
        success {
            echo '🚀 SUCCESS: Full DataOps lifecycle complete!'
        }
        failure {
            echo '❌ FAILURE: Check logs. If "sudo" failed, remember to run visudo on the host.'
        }
    }
}
