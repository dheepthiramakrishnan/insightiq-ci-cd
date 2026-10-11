pipeline {
    agent any

    environment {
        // CHANGE THIS to your Docker Hub username
        DOCKERHUB_USER = 'dheepthiramu'
        IMAGE_NAME     = "${DOCKERHUB_USER}/insightiq"
        IMAGE_TAG      = "${BUILD_NUMBER}"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Test') {
            steps {
                // Runs pytest inside the Dockerfile "test" stage; the build fails if any test fails
                sh 'docker build --target test -t ${IMAGE_NAME}:test .'
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                  docker build --build-arg BUILD_NUMBER=${IMAGE_TAG} \
                    -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                      echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                      docker push ${IMAGE_NAME}:${IMAGE_TAG}
                      docker push ${IMAGE_NAME}:latest
                      docker logout
                    '''
                }
            }
        }

        stage('Deploy with Ansible') {
            steps {
                // Secrets stay in Jenkins; Ansible reads them from the environment
                withCredentials([
                    string(credentialsId: 'insightiq-db-password', variable: 'DB_PASSWORD'),
                    string(credentialsId: 'groq-api-key',          variable: 'GROQ_API_KEY'),
                    string(credentialsId: 'app-secret-key',        variable: 'APP_SECRET_KEY')
                ]) {
                    sh '''
                      ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
                        -e image_name=${IMAGE_NAME} -e image_tag=${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                  sleep 5
                  curl -fsS http://${APP_HOST:-localhost}:8000/health
                  curl -fsS http://${APP_HOST:-localhost}:8000/api/ping
                '''
            }
        }
    }

    post {
        success { echo "Deployed ${IMAGE_NAME}:${IMAGE_TAG} successfully." }
        failure { echo 'Pipeline failed. Check the stage logs above.' }
        always  { sh 'docker image prune -f || true' }
    }
}
