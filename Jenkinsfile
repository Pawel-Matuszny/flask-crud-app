pipeline {

    environment {
        GCP_PROJECT_ID = "pawel-matuszny-2"
        PROJECT_NAME = "pawel-flask-app"
        IMAGE = "eu.gcr.io/pawel-matuszny-2/pawel-flask-app"
        VERSION = "ver1.0"
        ZONE = "europe-central2-c"
        CLUSTER_NAME = "pawel-cluster"
    }
    
    agent any
    

    stages {
        
        stage('Lint dockerfile') {
            agent {
                docker {
                    image 'hadolint/hadolint:latest-debian'
                }
            }
            steps {
                sh 'hadolint Dockerfile | tee -a hadolint_lint.txt'
            }
        }

        stage('Build Image') {
            steps {
                script {
                    sh 'docker rmi $(docker images -f "dangling=true" -q)'
                    sh 'docker-compose -p "$PROJECT_NAME" build'
                }
            }
        }

        stage('Push image to GCR') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'GCLOUD_SERVICE_JSON', variable: 'GC_KEY')]) {
                        sh 'cat ${GC_KEY} | docker login -u _json_key --password-stdin https://eu.gcr.io'
                        sh 'docker push $IMAGE:$VERSION'
                    }
                }
            }
        }

        stage('Deploy App to kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'GCLOUD_SERVICE_JSON', variable: 'GC_KEY')]) {
                        sh 'gcloud auth activate-service-account --key-file=${GC_KEY}'
                        sh 'gcloud config set project $GCP_PROJECT_ID'
                        sh 'gcloud config set compute/zone $ZONE'
                        sh 'gcloud container clusters get-credentials $CLUSTER_NAME'
                        sh 'kubectl patch deployment $PROJECT_NAME --patch "spec:\n  template:\n    metadata:\n      labels:\n        build: !!str "$BUILD_NUMBER""'
                        sh 'kubectl apply -f kubernetes/.'
                    }
                }
            }
        }
    }
 }