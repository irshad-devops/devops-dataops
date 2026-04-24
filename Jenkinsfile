pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
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

                        withCredentials([
                            string(credentialsId: 'db-password', variable: 'DB_PASSWORD'),
                            file(credentialsId: 'gcp-key-secret', variable: 'GCP_KEY')
                        ]) {

                            sh '''
                                rm -f gcp-key.json
                                cp $GCP_KEY gcp-key.json

                                terraform init -input=false -no-color

                                export TF_VAR_db_password=$DB_PASSWORD
                                terraform apply -auto-approve -input=false
                            '''

                            sh 'rm -f gcp-key.json'
                        }
                    }
                }
            }
        }

        stage('Deploy & Sync') {
            steps {
                script {
                    echo 'Syncing files to local deployment path...'

                    withCredentials([
                        file(credentialsId: 'gcp-key-secret', variable: 'GCP_KEY')
                    ]) {

                        sh """
                            mkdir -p ${DEPLOY_PATH}/dags/ ${DEPLOY_PATH}/scripts/ ${DEPLOY_PATH}/config/

                            cp -r dags/* ${DEPLOY_PATH}/dags/
                            cp -r scripts/* ${DEPLOY_PATH}/scripts/

                            rm -f ${DEPLOY_PATH}/config/gcp-key.json
                            cp \$GCP_KEY ${DEPLOY_PATH}/config/gcp-key.json
                        """
                    }
                }
            }
        }

        stage('Start Orchestration Stack') {
            steps {
                script {
                    echo 'Starting Docker containers...'
                    sh "docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d"

                    echo 'Waiting 20s for Vault and DB initialization...'
                    sleep 20
                }
            }
        }

        stage('Store Secrets in Vault') {
            steps {
                script {
                    echo 'Storing DB credentials in Vault...'

                    withCredentials([
                        string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN'),
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {

                        sh '''
                            export VAULT_ADDR=http://127.0.0.1:8200

                            docker exec airflow-vault sh -c "
                                export VAULT_TOKEN=$VAULT_TOKEN &&
                                export VAULT_ADDR=http://127.0.0.1:8200 &&
                                vault secrets enable -path=airflow kv-v2 || true &&
                                vault kv put airflow/connections/postgres_default \
                                conn_uri=postgresql://postgres:$DB_PASSWORD@34.69.30.163:5432/airflow
                            "
                        '''
                    }
                }
            }
        }

        stage('DataOps Quality Gate') {
            steps {
                script {
                    echo 'Running data validation checks...'

                    def worker_id = sh(
                        script: "docker ps -qf 'name=airflow-worker' | head -n 1",
                        returnStdout: true
                    ).trim()

                    if (worker_id) {
                        echo "Container Found: ${worker_id}"

                        sh "docker exec ${worker_id} pip install great_expectations"

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
            echo '❌ FAILURE: Check logs. Pipeline failed during execution.'
        }
    }
}
