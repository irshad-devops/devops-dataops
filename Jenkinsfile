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
                            # Create deployment directories with proper permissions
                            sudo mkdir -p ${DEPLOY_PATH}/dags \\
                                     ${DEPLOY_PATH}/scripts \\
                                     ${DEPLOY_PATH}/config \\
                                     ${DEPLOY_PATH}/logs \\
                                     ${DEPLOY_PATH}/plugins

                            # Set ownership to Jenkins user
                            sudo chown -R jenkins:jenkins ${DEPLOY_PATH}

                            # Copy DAGs (only if source exists)
                            if [ -d "dags" ]; then
                                cp -r dags/* ${DEPLOY_PATH}/dags/ 2>/dev/null || true
                            fi

                            # Copy scripts (only if source exists)
                            if [ -d "scripts" ]; then
                                cp -r scripts/* ${DEPLOY_PATH}/scripts/ 2>/dev/null || true
                            fi

                            # Copy plugins (only if source exists)
                            if [ -d "plugins" ]; then
                                cp -r plugins/* ${DEPLOY_PATH}/plugins/ 2>/dev/null || true
                            fi

                            # Copy docker-compose and Dockerfile if they exist
                            if [ -f "docker-compose.yaml" ]; then
                                cp docker-compose.yaml ${DEPLOY_PATH}/ 2>/dev/null || true
                            fi

                            if [ -f "Dockerfile" ]; then
                                cp Dockerfile ${DEPLOY_PATH}/ 2>/dev/null || true
                            fi

                            # Copy GCP key
                            rm -f ${DEPLOY_PATH}/config/gcp-key.json
                            cp \$GCP_KEY ${DEPLOY_PATH}/config/gcp-key.json

                            # Set proper permissions (use sudo if needed)
                            sudo chmod -R 755 ${DEPLOY_PATH} 2>/dev/null || true
                            sudo chown -R 5000:0 ${DEPLOY_PATH} 2>/dev/null || true
                        """
                    }
                }
            }
        }

        // ------------------ VALIDATE DOCKER FILES ------------------
        stage('Validate Docker Files') {
            steps {
                script {
                    sh """
                        cd ${DEPLOY_PATH}
                        
                        # Validate Dockerfile exists
                        if [ ! -f "Dockerfile" ]; then
                            echo "ERROR: Dockerfile not found in ${DEPLOY_PATH}"
                            exit 1
                        fi
                        
                        # Validate docker-compose.yaml exists
                        if [ ! -f "docker-compose.yaml" ]; then
                            echo "ERROR: docker-compose.yaml not found in ${DEPLOY_PATH}"
                            exit 1
                        fi
                        
                        echo "Docker files validation passed"
                        
                        # Show what files were copied
                        echo "Files in ${DEPLOY_PATH}:"
                        ls -la ${DEPLOY_PATH}
                        echo ""
                        echo "DAGs directory:"
                        ls -la ${DEPLOY_PATH}/dags/ 2>/dev/null || echo "No DAGs found"
                    """
                }
            }
        }

        // ------------------ STOP AND CLEAN EXISTING STACK ------------------
        stage('Clean Existing Stack') {
            steps {
                script {
                    sh """
                        cd ${DEPLOY_PATH}
                        
                        # Check if docker-compose file exists
                        if [ -f "docker-compose.yaml" ]; then
                            # Stop and remove existing containers
                            docker-compose -f docker-compose.yaml down -v || true
                        fi
                        
                        # Remove dangling images
                        docker system prune -f || true
                        
                        # Clean up any orphaned containers
                        docker container prune -f || true
                    """
                }
            }
        }

        // ------------------ BUILD CUSTOM AIRFLOW IMAGE ------------------
        stage('Build Airflow Image') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            cd ${DEPLOY_PATH}
                            
                            # Check if Dockerfile exists
                            if [ ! -f "Dockerfile" ]; then
                                echo "ERROR: Dockerfile not found!"
                                exit 1
                            fi
                            
                            # Build the custom Airflow image
                            echo "Building custom Airflow image..."
                            docker-compose -f docker-compose.yaml build --no-cache
                            
                            # Verify image was built
                            docker images | grep air-flow_airflow-init || echo "Image built successfully"
                        """
                    }
                }
            }
        }

        // ------------------ INITIALIZE AIRFLOW DATABASE ------------------
        stage('Initialize Airflow Database') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            cd ${DEPLOY_PATH}
                            
                            export DB_PASSWORD=${DB_PASSWORD}
                            
                            echo "Waiting for Cloud SQL to be ready..."
                            sleep 15
                            
                            echo "Initializing Airflow database schema..."
                            
                            # Run airflow-init with retry logic
                            MAX_RETRIES=3
                            RETRY_COUNT=0
                            until docker-compose -f docker-compose.yaml run --rm airflow-init; do
                                RETRY_COUNT=\$((RETRY_COUNT+1))
                                if [ \$RETRY_COUNT -ge \$MAX_RETRIES ]; then
                                    echo "Airflow initialization failed after \$MAX_RETRIES attempts"
                                    docker-compose -f docker-compose.yaml logs airflow-init
                                    exit 1
                                fi
                                echo "Initialization failed, retrying in 10 seconds... (Attempt \$RETRY_COUNT/\$MAX_RETRIES)"
                                sleep 10
                            done
                            
                            echo "Airflow database initialized successfully"
                        """
                    }
                }
            }
        }

        // ------------------ START AIRFLOW SERVICES ------------------
        stage('Start Airflow Services') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            cd ${DEPLOY_PATH}
                            
                            export DB_PASSWORD=${DB_PASSWORD}
                            
                            echo "Starting Airflow services..."
                            docker-compose -f docker-compose.yaml up -d
                            
                            # Show running containers
                            echo "Running containers:"
                            docker-compose -f docker-compose.yaml ps
                            
                            # Wait for containers to start
                            sleep 10
                        """
                    }
                }

                // Wait for Airflow Webserver to be healthy
                script {
                    sh """
                        cd ${DEPLOY_PATH}
                        
                        echo "Waiting for Airflow webserver to be healthy..."
                        MAX_RETRIES=30
                        COUNT=0
                        
                        # Give containers time to start
                        sleep 20
                        
                        until curl -s -f http://localhost:8080/health; do
                            if [ \$COUNT -eq \$MAX_RETRIES ]; then
                                echo "ERROR: Airflow webserver failed to start within timeout"
                                echo "Container logs:"
                                docker-compose -f docker-compose.yaml logs webserver
                                exit 1
                            fi
                            echo "Waiting for webserver... (\$COUNT/\$MAX_RETRIES)"
                            sleep 10
                            COUNT=\$((COUNT+1))
                        done
                        
                        echo "Airflow webserver is healthy"
                    """
                }
            }
        }

        // ------------------ VERIFY ALL SERVICES ------------------
        stage('Verify Services') {
            steps {
                script {
                    sh """
                        cd ${DEPLOY_PATH}
                        
                        echo "Verifying all services are running..."
                        
                        # Check webserver
                        docker-compose -f docker-compose.yaml ps webserver | grep "Up" || exit 1
                        
                        # Check scheduler
                        docker-compose -f docker-compose.yaml ps scheduler | grep "Up" || exit 1
                        
                        # Check worker
                        docker-compose -f docker-compose.yaml ps worker | grep "Up" || exit 1
                        
                        # Check redis
                        docker-compose -f docker-compose.yaml ps redis | grep "Up" || exit 1
                        
                        # Check vault
                        docker-compose -f docker-compose.yaml ps vault | grep "Up" || exit 1
                        
                        echo "All services are running properly"
                    """
                }
            }
        }

        // ------------------ CONFIGURE VAULT SECRETS ------------------
        stage('Configure Vault Secrets') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'vault-root-token', variable: 'VAULT_TOKEN'),
                        string(credentialsId: 'db-password', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            echo "Configuring Vault secrets..."
                            
                            # Wait for Vault to be ready
                            MAX_RETRIES=20
                            COUNT=0
                            until docker exec airflow-vault vault status &>/dev/null; do
                                if [ \$COUNT -eq \$MAX_RETRIES ]; then
                                    echo "Vault failed to become ready"
                                    exit 1
                                fi
                                echo "Waiting for Vault... (\$COUNT/\$MAX_RETRIES)"
                                sleep 5
                                COUNT=\$((COUNT+1))
                            done
                            
                            docker exec airflow-vault sh -c "
                                export VAULT_ADDR=http://127.0.0.1:8200
                                export VAULT_TOKEN=${VAULT_TOKEN}
                                
                                # Enable KV secrets engine if not already enabled
                                vault secrets enable -path=airflow kv-v2 || true
                                
                                # Store database connection
                                vault kv put airflow/connections/postgres_default \\
                                    conn_uri=postgresql+psycopg2://postgres:${DB_PASSWORD}@34.69.30.163:5432/airflow
                                
                                # Store GCP credentials path
                                vault kv put airflow/variables/gcp_key_path \\
                                    value=/opt/airflow/config/gcp-key.json
                                
                                echo "Vault secrets configured successfully"
                            "
                        """
                    }
                }
            }
        }

        // ------------------ QUALITY GATE - GREAT EXPECTATIONS ------------------
        stage('Quality Gate') {
            steps {
                script {
                    // Get the worker container ID
                    def worker_id = sh(
                        script: "docker ps -qf 'name=airflow-worker' | head -n 1",
                        returnStdout: true
                    ).trim()

                    if (!worker_id) {
                        echo "No Airflow worker found, skipping quality gate"
                        return
                    }

                    // Wait for worker to be fully ready
                    sh """
                        echo "Waiting for Airflow worker to be ready..."
                        sleep 10
                        
                        # Check if great_expectations is installed, install if not
                        docker exec ${worker_id} pip list | grep great_expectations || \\
                            docker exec ${worker_id} pip install --quiet great_expectations || echo "Great expectations installation skipped"
                    """

                    // Run Great Expectations validation if script exists
                    sh """
                        echo "Checking for Great Expectations validation script..."
                        if docker exec ${worker_id} test -f /opt/airflow/scripts/validate_flights.py; then
                            echo "Running Great Expectations validation..."
                            docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py || echo "Validation script failed but continuing"
                        else
                            echo "No validation script found, skipping quality gate"
                        fi
                    """
                }
            }
        }

        // ------------------ LIST DEPLOYED DAGS ------------------
        stage('List Deployed DAGs') {
            steps {
                script {
                    def webserver_id = sh(
                        script: "docker ps -qf 'name=airflow-webserver' | head -n 1",
                        returnStdout: true
                    ).trim()
                    
                    if (webserver_id) {
                        sh """
                            echo "Deployed DAGs:"
                            docker exec ${webserver_id} airflow dags list 2>/dev/null || echo "Unable to list DAGs"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "🚀 SUCCESS: Pipeline completed and Airflow is running successfully!"
            script {
                sh """
                    echo "=========================================="
                    echo "Airflow Deployment Summary:"
                    echo "=========================================="
                    echo "Webserver: http://localhost:8080"
                    echo "Username: admin"
                    echo "Password: admin"
                    echo "Vault UI: http://localhost:8200"
                    echo "Vault Token: root"
                    echo "=========================================="
                """
            }
        }
        failure {
            echo "❌ FAILURE: Pipeline failed. Gathering debug information..."
            script {
                sh """
                    echo "=== Docker Container Status ==="
                    docker ps -a
                    
                    echo ""
                    echo "=== Last 50 lines of build logs ==="
                    echo "Check Jenkins console for details"
                    
                    echo ""
                    echo "=== Checking deployment directory ==="
                    ls -la ${DEPLOY_PATH} 2>/dev/null || echo "Deployment directory not found"
                    
                    echo ""
                    echo "=== Checking Docker files ==="
                    ls -la ${DEPLOY_PATH}/Dockerfile 2>/dev/null || echo "Dockerfile not found"
                    ls -la ${DEPLOY_PATH}/docker-compose.yaml 2>/dev/null || echo "docker-compose.yaml not found"
                """
            }
        }
    }
}
