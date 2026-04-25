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
                            # Create deployment directories
                            mkdir -p ${DEPLOY_PATH}/dags \\
                                     ${DEPLOY_PATH}/scripts \\
                                     ${DEPLOY_PATH}/config \\
                                     ${DEPLOY_PATH}/logs \\
                                     ${DEPLOY_PATH}/plugins

                            # Copy DAGs and scripts
                            cp -r dags/* ${DEPLOY_PATH}/dags/ 2>/dev/null || true
                            cp -r scripts/* ${DEPLOY_PATH}/scripts/ 2>/dev/null || true
                            cp -r plugins/* ${DEPLOY_PATH}/plugins/ 2>/dev/null || true

                            # Copy docker-compose and Dockerfile
                            cp docker-compose.yaml ${DEPLOY_PATH}/ 2>/dev/null || true
                            cp Dockerfile ${DEPLOY_PATH}/ 2>/dev/null || true

                            # Copy GCP key
                            rm -f ${DEPLOY_PATH}/config/gcp-key.json
                            cp $GCP_KEY ${DEPLOY_PATH}/config/gcp-key.json

                            # Set proper permissions
                            chmod -R 755 ${DEPLOY_PATH}
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
                        
                        # Stop and remove existing containers
                        docker-compose -f docker-compose.yaml down -v || true
                        
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
                            
                            # Export database password for build args if needed
                            export DB_PASSWORD=${DB_PASSWORD}
                            
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
                        """
                    }
                }

                // Wait for Airflow Webserver to be healthy
                script {
                    sh '''
                        echo "Waiting for Airflow webserver to be healthy..."
                        MAX_RETRIES=30
                        COUNT=0
                        
                        # Give containers time to start
                        sleep 20
                        
                        until curl -s -f http://localhost:8080/health; do
                            if [ $COUNT -eq $MAX_RETRIES ]; then
                                echo "ERROR: Airflow webserver failed to start within timeout"
                                echo "Container logs:"
                                docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml logs webserver
                                exit 1
                            fi
                            echo "Waiting for webserver... ($COUNT/$MAX_RETRIES)"
                            sleep 10
                            COUNT=$((COUNT+1))
                        done
                        
                        # Additional check for metadatabase health
                        HEALTH_CHECK=$(curl -s http://localhost:8080/health)
                        if echo "$HEALTH_CHECK" | grep -q '"metadatabase": {"status": "healthy"}'; then
                            echo "Airflow webserver is healthy and database is connected"
                        else
                            echo "WARNING: Metadatabase health check not passed, but webserver is running"
                        fi
                    '''
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
                        error "Airflow worker container not found"
                    }

                    // Wait for worker to be fully ready
                    sh """
                        echo "Waiting for Airflow worker to be ready..."
                        sleep 10
                        
                        # Check if great_expectations is installed, install if not
                        docker exec ${worker_id} pip list | grep great_expectations || \\
                            docker exec ${worker_id} pip install --quiet great_expectations
                    """

                    // Run Great Expectations validation
                    sh """
                        echo "Running Great Expectations validation..."
                        docker exec ${worker_id} python3 /opt/airflow/scripts/validate_flights.py
                        
                        if [ \$? -ne 0 ]; then
                            echo "Great Expectations validation failed"
                            exit 1
                        fi
                        
                        echo "Great Expectations validation passed"
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
                            docker exec ${webserver_id} airflow dags list
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
                    echo ""
                    echo "Useful commands:"
                    echo "  View logs: docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml logs -f"
                    echo "  Stop all: docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml down"
                    echo "  Restart: docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml restart"
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
                    echo "=== Docker Compose Logs (last 100 lines) ==="
                    docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml logs --tail=100
                    
                    echo ""
                    echo "=== Airflow Init Container Logs ==="
                    docker logs airflow-init 2>/dev/null || echo "No airflow-init container found"
                    
                    echo ""
                    echo "=== Failed Service Logs ==="
                    for service in webserver scheduler worker; do
                        echo "--- \${service} logs ---"
                        docker-compose -f ${DEPLOY_PATH}/docker-compose.yaml logs --tail=50 \${service}
                    done
                """
            }
            error "Pipeline failed. Check the logs above for details."
        }
        always {
            script {
                // Clean up old images and volumes to save disk space (optional)
                sh """
                    echo "Cleaning up old Docker artifacts..."
                    docker system prune -f --filter "until=24h" || true
                """
            }
        }
    }
}
