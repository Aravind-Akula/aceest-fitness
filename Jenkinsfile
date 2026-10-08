pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Clean Build') {
            steps {
                sh 'docker build --no-cache -t aceest-fitness:${BUILD_NUMBER} .'
            }
        }
        stage('Test in Container') {
            steps {
                sh 'docker run --rm aceest-fitness:${BUILD_NUMBER} pytest -v'
            }
        }
    }
    post {
        always { sh 'docker image prune -f || true' }
    }
}
