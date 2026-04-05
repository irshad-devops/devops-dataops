pipeline {
    agent any

    environment {
        // Path where your Airflow Docker/Local setup is running
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        
        // Caching Terraform plugins to speed up repeat runs
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        
        // This pulls the GCP JSON key from your Jenkins Credentials store
        GCP_KEY = credentials('gcp-key-secret')
        
        // Defining the missing variable here so Terraform is happy
        DB_PASSWORD = "MarwatSecurePass123!" 
    }

    stages {
        stage('Checkout') {
            steps {
                // Pulls the latest code from your repository
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Infrastructure Update') {
            steps {
                dir('terraform') {
                    // 1. Prepare environment
                    sh 'mkdir -p ${TF_PLUGIN_CACHE_DIR}'
                    
                    // 2. Temporarily copy the secret key for Terraform to use
                    // We use single quotes and double-dash to handle the path safely
                    sh 'cp "${GCP_KEY}" ./gcp-key.json'
                    
                    // 3. Initialize Terraform
                    sh 'terraform init -input=false -no-color'
                    
                    // 4. Apply changes. 
                    // Note: We pass the db_password variable here to fix your error
                    sh 'terraform apply -auto-approve -input=false -var="db_password=${DB_PASSWORD}"'
                    
                    // 5. Clean up the sensitive key from the workspace
                    sh 'rm ./gcp-key.json'
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                // Ensure the target folders exist on your machine
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                
                // Copy DAGs (Orchestration)
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                
                // Copy Spark/Python Scripts (Transformation)
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                
                // Copy the GCP Key to the Airflow config folder 
                // This allows the Airflow Worker to authenticate with Google Cloud
                sh 'cp "${GCP_KEY}" ' + "${DEPLOY_PATH}/config/gcp-key.json"
                
                echo 'Deployment Complete!'
            }
        }
    }
    
    post {
        success {
            echo 'SUCCESS: Pipeline deployed and infrastructure verified!'
        }
        failure {
            echo 'FAILURE: Check the logs above. Likely a permission issue or Terraform variable error.'
        }
    }
}
