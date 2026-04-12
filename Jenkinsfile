pipeline {
    agent any

    environment {
        // Path on the host machine where the stack resides
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        GCP_KEY = credentials('gcp-key-secret')
        DB_PASSWORD = "MarwatSecurePass123!" 
        VAULT_TOKEN = "root" 
    }

    stages {
        stage('Checkout') {
            steps {
                // Pulls code from your repository
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    script {
                        echo 'Starting Infrastructure Management...'
                        sh 'rm -f ./gcp-key.json'
                        sh 'cp "${GCP_KEY}" ./gcp-key.json'
                        
                        // Handles network blips/DNS timeouts automatically
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
                    echo 'Deploying DAGs and Scripts...'
                    // Ensure the directory exists and the Jenkins user can write to it
                    sh "sudo mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                    sh "sudo chown -R jenkins:jenkins ${DEPLOY_PATH}"
                    
                    // Copy files from Jenkins workspace to the Airflow deployment path
                    sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                    sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                    
                    // Securely move the GCP key for Airflow container use
                    sh "rm -f ${DEPLOY_PATH}/config/gcp-key.json"
                    sh 'cp "${GCP_KEY}" ' + "${DEPLOY_PATH}/config/gcp-key.json"
                }
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                // Launch the Docker containers in detached mode
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                echo 'Waiting 20s for services (Vault/Postgres) to warm up...'
                sleep 20 
            }
        }

        stage('Security & Secrets (Vault)') {
            steps {
                script {
                    echo 'Automating Secret Injection into Vault...'
                    // Pass Vault Token/Addr as ENV vars to the 'docker exec' to prevent 403 Forbidden errors
                    sh """
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault secrets enable -path=airflow kv-v2 || true
                        
                        docker exec -e VAULT_TOKEN=${VAULT_TOKEN} -e VAULT_ADDR='http://127.0.0.1:8200' airflow-vault vault kv put airflow/connections/postgres_default \
                        conn_uri='postgresql://airflow:airflow@postgres:5432/airflow'
                    """
                    echo '✅ Success: Connection string secured in HashiCorp Vault.'
                }
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    echo 'Running Quality Gate Validation...'
                    // Dynamically find the worker container to run the validation script
                    def worker_id = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()
                    if (worker_id) {
                        echo "Executing validation inside Container: ${worker_id}"
                        sh "docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py"
                    } else {
                        error "CRITICAL: Airflow Worker container not found. Check Docker health."
                    }
                }
            }
        }
    }

    post {
        success {
            echo '🚀 SUCCESS: The entire DataOps pipeline is deployed, secured, and validated!'
        }
        failure {
            echo '❌ FAILURE: Pipeline failed. Check the logs above for permission or connection errors.'
        }
    }
}
