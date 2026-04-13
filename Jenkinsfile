pipeline {
    agent any

    environment {
        AWS_REGION     = 'us-east-1'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        GEMINI_API_KEY = credentials('GEMINI_API_KEY')
        SECRET_KEY     = credentials('FLASK_SECRET_KEY')
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        EC2_KEY_PAIR_NAME     = credentials('EC2_KEY_NAME')  // secret text: just the key pair name e.g. "my-key"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Terraform Init & Apply') {
            steps {
                dir('deploy') {
                    sh '''
                        terraform init -input=false
                        terraform apply -input=false -auto-approve \
                            -var="key_name=${EC2_KEY_PAIR_NAME}" \
                            -var="aws_region=${AWS_REGION}"
                    '''
                    sh '''
                        terraform output -raw ec2_public_ip  > ../ec2_ip.txt
                        terraform output -raw ecr_repo_url   > ../ecr_repo.txt
                    '''
                }
                script {
                    env.EC2_IP   = readFile('ec2_ip.txt').trim()
                    env.ECR_REPO = readFile('ecr_repo.txt').trim()
                }
                // Write .pem from Jenkins SSH credential so all downstream stages can use it
                sshagent(['ec2-ssh-key']) {
                    sh '''
                        mkdir -p ~/.ssh
                        ssh-add -L > ~/.ssh/ec2-deploy.pem
                        chmod 400 ~/.ssh/ec2-deploy.pem
                    '''
                }
                echo "EC2 IP: ${env.EC2_IP}"
                echo "ECR Repo: ${env.ECR_REPO}"
            }
        }

        stage('Wait for EC2') {
            steps {
                sh '''
                    echo "Waiting for EC2 to be ready..."
                    for i in $(seq 1 20); do
                        if ssh -o StrictHostKeyChecking=no \
                               -o ConnectTimeout=5 \
                               -i ~/.ssh/ec2-deploy.pem \
                               ubuntu@${EC2_IP} "docker --version" 2>/dev/null; then
                            echo "EC2 is ready"
                            exit 0
                        fi
                        echo "Attempt $i/20 — waiting 15s..."
                        sleep 15
                    done
                    echo "EC2 did not become ready in time"
                    exit 1
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ai-career-coach:${IMAGE_TAG} ."
            }
        }

        stage('Push to ECR') {
            steps {
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

        stage('Generate Ansible Inventory') {
            steps {
                sh """
                    cat > ansible/inventory.ini <<EOF
[ec2]
${EC2_IP} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/ec2-deploy.pem ansible_ssh_common_args='-o StrictHostKeyChecking=no'
EOF
                """
            }
        }

        stage('Deploy via Ansible') {
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
            echo "=========================================="
            echo "Deployment successful!"
            echo "App URL: http://${env.EC2_IP}:5000"
            echo "Image:   ${env.ECR_REPO}:${IMAGE_TAG}"
            echo "=========================================="
        }
        failure {
            echo "Deployment failed — check stage logs above"
        }
        always {
            sh "docker rmi ai-career-coach:${IMAGE_TAG} || true"
            sh "rm -f ec2_ip.txt ecr_repo.txt"
        }
    }
}
