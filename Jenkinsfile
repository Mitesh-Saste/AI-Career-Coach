pipeline {
    agent any

    environment {
        AWS_REGION      = 'us-east-1'
        ECR_REPO        = '<your-aws-account-id>.dkr.ecr.ap-south-1.amazonaws.com/ai-career-coach'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        EC2_USER        = 'ubuntu'
        EC2_HOST        = credentials('EC2_HOST')         // EC2 public IP stored in Jenkins credentials
        GEMINI_API_KEY  = credentials('GEMINI_API_KEY')   // Gemini API key stored in Jenkins credentials
        SECRET_KEY      = credentials('FLASK_SECRET_KEY') // Flask secret key stored in Jenkins credentials
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ai-career-coach:${IMAGE_TAG} ."
            }
        }

        stage('Push to ECR') {
            steps {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-credentials') {
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} \
                            | docker login --username AWS --password-stdin ${ECR_REPO}
                        docker tag ai-career-coach:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}
                        docker tag ai-career-coach:${IMAGE_TAG} ${ECR_REPO}:latest
                        docker push ${ECR_REPO}:${IMAGE_TAG}
                        docker push ${ECR_REPO}:latest
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
                            -e "ecr_repo=${ECR_REPO}" \
                            -e "image_tag=${IMAGE_TAG}" \
                            -e "aws_region=${AWS_REGION}" \
                            -e "gemini_api_key=${GEMINI_API_KEY}" \
                            -e "secret_key=${SECRET_KEY}"
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployment successful — image: ${ECR_REPO}:${IMAGE_TAG}"
        }
        failure {
            echo "Deployment failed — check logs above"
        }
        always {
            sh "docker rmi ai-career-coach:${IMAGE_TAG} || true"
        }
    }
}
