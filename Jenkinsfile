pipeline {
    agent any

    environment {
        // Define your Airflow deployment path
        DEPLOY_PATH = "/home/marwat/Documents/Air-flow"
        // Helps avoid re-downloading plugins if registry is slow
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
    }

    stages {
        stage('Checkout') {
            steps {
                // Pulls the latest validated code from your repo
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataopd.git'
            }
        }

        stage('Infrastructure Update') {
            steps {
                dir('terraform') {
                    // Create cache directory to prevent timeout on repeat builds
                    sh 'mkdir -p ${TF_PLUGIN_CACHE_DIR}'
                    
                    // init with -get-plugins=false if you already have them locally
                    // or standard init with a longer timeout
                    sh 'terraform init -input=false -no-color'
                    
                    // Automates the Ops side: Terraform apply
                    sh 'terraform apply -auto-approve -input=false'
                }
            }
        }

        stage('Deploy to Airflow') {
            steps {
                // Ensure directories exist before copying
                sh "mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/"
                
                // Syncs your DAGs and Scripts to the live server
                sh "cp -r dags/* ${DEPLOY_PATH}/dags/"
                sh "cp -r scripts/* ${DEPLOY_PATH}/scripts/"
                
                echo 'Deployment Complete!'
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline deployed successfully to Airflow!'
        }
        failure {
            echo 'Pipeline failed. Check Terraform connectivity or folder permissions.'
        }
    }
}
