pipeline {
    agent any

    environment {
        // AWS 설정 - Jenkins에서 AWS 자격 증명 설정 필요
        AWS_DEFAULT_REGION = 'ap-northeast-2'
        // 또는 Jenkins에서 AWS 자격 증명을 설정한 경우 아래 주석 해제
        // AWS_ACCESS_KEY_ID = credentials('aws-access-key-id')
        // AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        
        // 프로덕션 환경 설정
        ENVIRONMENT = 'prod'
        CORS_ORIGINS = 'http://54.180.71.13:3000,http://54.180.71.13:5173,https://buildpechatbot.com'
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


