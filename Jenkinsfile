pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/marwat/Documents/gcp-lab/Air-flow"
        GCP_KEY = credentials('gcp-key-secret')
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/irshad-devops/devops-dataops.git'
            }
        }

        stage('Terraform (GCP Infra)') {
            steps {
                dir('terraform') {
                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASS')
                    ]) {
                        sh '''
                        cp "${GCP_KEY}" ./gcp-key.json

                        terraform init -input=false
                        terraform apply -auto-approve \
                          -var="db_password=${DB_PASS}"

                        rm -f ./gcp-key.json
                        '''
                    }
                }
            }
        }

        stage('Deploy Docker Stack') {
            steps {
                sh """
                docker compose -f ${DEPLOY_PATH}/docker-compose.yaml down
                docker compose -f ${DEPLOY_PATH}/docker-compose.yaml up -d --build
                """
                sleep 20
            }
        }

        stage('Inject Secrets into Vault') {
            steps {
                withCredentials([
                    string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN'),
                    string(credentialsId: 'db-password', variable: 'DB_PASS')
                ]) {
                    sh '''
                    docker exec airflow-vault sh -c "
                    export VAULT_ADDR=http://127.0.0.1:8200
                    export VAULT_TOKEN=${VAULT_TOKEN}

                    vault secrets enable -path=airflow kv-v2 || true

                    vault kv put airflow/connections/postgres_default \
                    conn_uri='postgresql://postgres:${DB_PASS}@cloudsql-proxy:5432/airflow'
                    "
                    '''
                }
            }
        }

        stage('Data Quality Check') {
            steps {
                script {
                    def worker = sh(script: "docker ps -qf 'name=airflow-worker' | head -n 1", returnStdout: true).trim()

                    if (worker) {
                        sh "docker exec ${worker} python3 /opt/airflow/scripts/validate_flights.py"
                    } else {
                        error "Airflow worker not running"
                    }
                }
            }
        }
    }

    post {
        success {
            echo '🚀 SUCCESS: Full pipeline completed'
        }
        failure {
            echo '❌ FAILURE: Check logs'
        }
    }
}
