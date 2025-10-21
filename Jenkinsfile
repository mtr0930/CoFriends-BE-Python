pipeline {
    agent any

    environment {
        // AWS 설정 - IAM Role 사용 (EC2 인스턴스에 IAM Role 할당 필요)
        AWS_DEFAULT_REGION = 'ap-northeast-2'
        // IAM Role을 사용하므로 Jenkins에서 AWS 자격 증명 설정 불필요
        ENVIRONMENT = 'prod'
        CORS_ORIGINS = 'http://54.180.71.13:3000,http://54.180.71.13:5173,https://buildpechatbot.com:5000,https://buildpechatbot.com:5173'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Check Environment') {
            steps {
                // 필요한 파일 존재 확인
                sh 'test -f Dockerfile'
                sh 'test -f docker-compose.yml'
                sh 'test -f requirements.txt'
                // AWS CLI 설치 확인 (Secrets Manager 접근용)
                sh 'aws --version || echo "AWS CLI not found - make sure AWS credentials are configured"'
            }
        }
        stage('Cleanup Docker') {
            steps {
                sh 'docker system prune -af --volumes'
            }
        }
        stage('Docker Build') {
            steps {
                sh 'docker compose up -d --force-recreate --build fastapi-app'
            }
        }
        stage('Docker Run') {
            steps {
                sh 'docker stop cofriends-fastapi || true'
                sh 'docker rm -f cofriends-fastapi || true'
                sh 'docker compose up -d fastapi-app'
            }
        }
    }
}


