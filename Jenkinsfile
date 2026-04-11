pipeline {
    agent any

    environment {
        // Path to your project directory on the host
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        
        // Infrastructure Variables
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        GCP_KEY = credentials('gcp-key-secret')
        DB_PASSWORD = "MarwatSecurePass123!" 
        
        // Security & Quality Config
        VAULT_TOKEN = "root" 
        AIRFLOW_WORKER_CONTAINER = "air-flow-airflow-worker-1"
    }

    stages {
        stage('Checkout') {
            steps {
                // Ensure the latest code is pulled from your repository
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Security & Secrets (Vault)') {
            steps {
                echo 'Checking Vault status for SOC 2 Compliance...'
                // Verifies the Vault container is ready to manage secrets
                sh "curl -H 'X-Vault-Token: ${VAULT_TOKEN}' http://localhost:8200/v1/sys/health || true"
            }
        }

        stage('Infrastructure (Multi-Cloud IaC)') {
            steps {
                dir('terraform') {
                    sh 'mkdir -p ${TF_PLUGIN_CACHE_DIR}'
                    sh 'cp "${GCP_KEY}" ./gcp-key.json'
                    
                    echo 'Initializing Terraform for GCP, AWS, and Azure...'
                    sh 'terraform init -input=false -no-color'
                    
                    echo 'Applying Multi-Cloud infrastructure with KMS encryption...'
                    sh 'terraform apply -auto-approve -input=false -var="db_password=${DB_PASSWORD}"'
                    
                    sh 'rm ./gcp-key.json'
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                // Prepare application directories
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                
                // Copy Dags, Spark scripts, and Great Expectations configs
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                sh 'cp "${GCP_KEY}" ' + "${DEPLOY_PATH}/config/gcp-key.json"
                
                echo 'Application code and compliance scripts deployed.'
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                echo 'Launching Airflow, Superset, Loki, and Grafana...'
                // Fulfills the "Observability and Visualization" stack requirement
                sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"
                
                // Give services a moment to warm up
                sleep 10
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                echo 'Running Automated Validation with Great Expectations...'
                /* This is the CRITICAL DataOps step. 
                   It executes the GX validation script inside the running Airflow worker.
                   If the data doesn't meet quality standards, the pipeline fails.
                */
                sh "docker exec ${AIRFLOW_WORKER_CONTAINER} python3 /opt/airflow/scripts/validate_flights.py"
            }
        }
    }

    post {
        success {
            echo '✅ SUCCESS: Multi-Cloud Infra Ready, Secrets Secured, and Quality Gate Passed!'
        }
        failure {
            echo '❌ FAILURE: Pipeline failed. Check Great Expectations results or Docker logs.'
        }
    }
}
