pipeline {
    agent any

    environment {
        // Corrected path based on your previous 'ls' output
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
        // Use the Jenkins Credential ID we created earlier
        GCP_KEY = credentials('gcp-key-secret') 
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataopd.git'
            }
        }

        stage('Infrastructure Update') {
            steps {
                dir('terraform') {
                    sh 'mkdir -p ${TF_PLUGIN_CACHE_DIR}'
                    
                    // Temporarily copy the secret key into the terraform folder for the run
                    sh "cp ${GCP_KEY} ./marwat-project-key.json"
                    
                    sh 'terraform init -input=false -no-color'
                    sh 'terraform apply -auto-approve -input=false'
                    
                    // Clean up the key immediately after apply for security
                    sh "rm ./marwat-project-key.json"
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/"
                
                // Deploy Code
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                
                // Deploy the key to the Airflow config folder so the Worker can use it
                sh "cp ${GCP_KEY} ${DEPLOY_PATH}/config/gcp-key.json"
                
                echo 'Deployment Complete!'
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline deployed successfully to Airflow!'
        }
        failure {
            echo 'Pipeline failed. Check Jenkins Console Output for details.'
        }
    }
}
