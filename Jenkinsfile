pipeline {
    agent any

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


