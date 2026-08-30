pipeline {
    agent {
        kubernetes {
            yaml '''
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: python-tester
                image: python:3.12-slim
                command: ['sleep']
                args: ['infinity']
                env:
                - name: POSTGRES_SERVER
                  value: "localhost"
                - name: POSTGRES_USER
                  value: "postgres"
                - name: POSTGRES_PASSWORD
                  value: "postgres"
                - name: POSTGRES_DB
                  value: "app"
                - name: POSTGRES_PORT
                  value: "5432"
                - name: REDIS_HOST
                  value: "localhost"
                - name: REDIS_PORT
                  value: "6379"
                - name: REDIS_PASSWORD
                  value: "secure_redis_password"
                - name: SECRET_KEY
                  value: "test_secret_key_1234567890_for_ci"
                resources:
                  requests:
                    cpu: "1500m"
                    memory: "1Gi"
                  limits:
                    cpu: "1500m"
                    memory: "1Gi"
              - name: postgres
                image: postgres:15-alpine
                env:
                - name: POSTGRES_USER
                  value: "postgres"
                - name: POSTGRES_PASSWORD
                  value: "postgres"
                - name: POSTGRES_DB
                  value: "app"
                ports:
                - containerPort: 5432
              - name: redis
                image: redis:7-alpine
                command: ["redis-server"]
                args: ["--requirepass", "secure_redis_password"]
                ports:
                - containerPort: 6379
              - name: kaniko
                image: gcr.io/kaniko-project/executor:debug
                command: ['sleep']
                args: ['infinity']
                volumeMounts:
                - name: docker-config
                  mountPath: /kaniko/.docker/
              volumes:
              - name: docker-config
                secret:
                  secretName: registry-credentials
            '''
        }
    }
    
    environment {
        IMAGE_NAME = "your-registry/backend"
        IMAGE_TAG = "${env.GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Preparation (Bước Trước)') {
            steps {
                container('python-tester') {
                    dir('backend') {
                        // Cài đặt thư viện 1 lần duy nhất để các luồng song song phía sau sử dụng chung
                        sh '''
                        pip install --require-hashes -r requirements.txt
                        pip install --require-hashes -r requirements-dev.txt
                        '''
                    }
                }
            }
        }
        
        stage('Verification (Chạy Song Song)') {
            failFast true // Lệnh này ép: Nếu 1 nhánh tạch, giết ngay các nhánh còn lại để tiết kiệm tài nguyên
            
            parallel {
                stage('Lint & Format') {
                    steps {
                        container('python-tester') {
                            dir('backend') {
                                sh '''
                                black --check app tests
                                isort --check-only app tests
                                flake8 app tests --max-line-length=88
                                '''
                            }
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        container('python-tester') {
                            dir('backend') {
                                sh 'bandit -r app/'
                            }
                        }
                    }
                }
                
                stage('Unit Testing') {
                    steps {
                        container('python-tester') {
                            dir('backend') {
                                sh '''
                                # Chờ Database & Redis khởi động
                                sleep 5
                                pytest tests/ --cov=app --cov-report=xml
                                '''
                            }
                        }
                    }
                }
            }
        }
        
        stage('Build & Push (Kaniko)') {
            steps {
                container('kaniko') {
                    sh '''
                    /kaniko/executor \
                      --context $(pwd) \
                      --dockerfile $(pwd)/backend/Dockerfile.prod \
                      --destination ${IMAGE_NAME}:${IMAGE_TAG} \
                      --cache=true
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo "✅ Image ${IMAGE_NAME}:${IMAGE_TAG} is ready."
        }
        failure {
            echo "❌ Failed."
        }
    }
}
