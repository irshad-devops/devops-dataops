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
                echo 'Checking Vault status...'
                sh "curl -H 'X-Vault-Token: ${VAULT_TOKEN}' http://localhost:8200/v1/sys/health || true"
            }
        }

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    // FORCE CLEANUP: Remove old key if it exists to avoid 'Permission Denied'
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
                // Clean and copy key to the Airflow config directory
                sh "rm -f ${DEPLOY_PATH}/config/gcp-key.json"
                sh 'cp "${GCP_KEY}" ' + "${DEPLOY_PATH}/config/gcp-key.json"
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                sleep 15 // Increased slightly to ensure worker is fully up
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    echo 'Finding Airflow Worker Container dynamically...'
                    // This command finds the container ID for the worker regardless of name (hyphen vs underscore)
                    def worker_id = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()
                    
                    if (worker_id) {
                        echo "Targeting Container ID: ${worker_id}"
                        sh "docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py"
                    } else {
                        error "FAIL: Airflow Worker container not found. Check 'docker ps' manually."
                    }
                }
            }
        }
    }

    post {
        success { echo '✅ SUCCESS: Pipeline Completed!' }
        failure { echo '❌ FAILURE: Check logs for permission or validation errors.' }
    }
}
