pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        TF_PLUGIN_CACHE_DIR = "${WORKSPACE}/.terraform.d/plugin-cache"
    }

    stages {

        // ------------------ CHECKOUT ------------------
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        // ------------------ INFRA (Terraform) ------------------
        stage('Infrastructure (IaC)') {
            steps {
                dir('terraform') {
                    script {
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

                                rm -f gcp-key.json
                            '''
                        }
                    }
                }
            }
        }

        // ------------------ DEPLOY FILES ------------------
        stage('Deploy Files') {
            steps {
                script {
                    withCredentials([
                        file(credentialsId: 'gcp-key-secret', variable: 'GCP_KEY')
                    ]) {
                        sh """
                            mkdir -p ${DEPLOY_PATH}/dags \
                                     ${DEPLOY_PATH}/scripts \
                                     ${DEPLOY_PATH}/config

                            cp -r dags/* ${DEPLOY_PATH}/dags/
                            cp -r scripts/* ${DEPLOY_PATH}/scripts/

                            rm -f ${DEPLOY_PATH}/config/gcp-key.json
                            cp \$GCP_KEY ${DEPLOY_PATH}/config/gcp-key.json
                        """
                    }
                }
            }
        }

        // ------------------ START STACK ------------------
        stage('Start Stack') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {

                        sh """
                            set -e

                            export DB_PASSWORD=${DB_PASSWORD}

                            docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml down -v || true
                            docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d
                        """
                    }
                }

                // Wait for Airflow
                sh '''
                    echo "Waiting for Airflow..."
                    until curl -s http://localhost:8080/health | grep '"metadatabase": {"status": "healthy"}'; do
                        sleep 5
                    done
                '''
            }
        }

        // ------------------ VAULT SECRETS ------------------
        stage('Vault Secrets') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN'),
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {

                        sh '''
                            docker exec airflow-vault sh -c "
                                export VAULT_ADDR=http://127.0.0.1:8200 &&
                                export VAULT_TOKEN=$VAULT_TOKEN &&

                                vault secrets enable -path=airflow kv-v2 || true &&

                                vault kv put airflow/connections/postgres_default \
                                conn_uri=postgresql+psycopg2://postgres:$DB_PASSWORD@34.69.30.163:5432/airflow
                            "
                        '''
                    }
                }
            }
        }

        // ------------------ QUALITY GATE ------------------
        stage('Quality Gate') {
            steps {
                script {
                    def worker_id = sh(
                        script: "docker ps -qf 'name=airflow-worker' | head -n 1",
                        returnStdout: true
                    ).trim()

                    if (!worker_id) {
                        error "Airflow worker not found"
                    }

                    sh """
                        docker exec ${worker_id} pip install --quiet great_expectations
                        docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🚀 SUCCESS: Pipeline completed!"
        }
        failure {
            echo "❌ FAILURE: Check logs"
        }
    }
}
