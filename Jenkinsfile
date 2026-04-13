pipeline {
    agent any

    environment {
        AWS_REGION     = 'us-east-1'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        GEMINI_API_KEY = credentials('GEMINI_API_KEY')
        SECRET_KEY     = credentials('FLASK_SECRET_KEY')
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Terraform Init & Apply') {
            steps {
                // Write private key and derive public key from Jenkins SSH credential
                withCredentials([sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'SSH_KEY_FILE')]) {
                    sh '''
                        cp "$SSH_KEY_FILE" ec2-deploy.pem
                        chmod 400 ec2-deploy.pem
                        ssh-keygen -y -f ec2-deploy.pem > ec2-deploy.pub
                    '''
                }
                dir('deploy') {
                    sh '''
                        terraform init -input=false
                        # Write public key to tfvars file with proper quoting
                        printf 'public_key = "%s"\n' "$(cat ${WORKSPACE}/ec2-deploy.pub)" > terraform.tfvars
                        printf 'aws_region = "%s"\n' "${AWS_REGION}" >> terraform.tfvars
                        terraform apply -input=false -auto-approve
                    '''
                    sh '''
                        terraform output -raw ec2_public_ip > ../ec2_ip.txt
                        terraform output -raw ecr_repo_url  > ../ecr_repo.txt
                    '''
                }
                script {
                    env.EC2_IP   = readFile('ec2_ip.txt').trim()
                    env.ECR_REPO = readFile('ecr_repo.txt').trim()
                }
                echo "EC2 IP: ${env.EC2_IP}"
                echo "ECR Repo: ${env.ECR_REPO}"
            }
        }

        stage('Wait for EC2') {
            steps {
                sh '''
                    echo "Waiting for SSH to be available..."
                    for i in $(seq 1 20); do
                        if ssh -o StrictHostKeyChecking=no \
                               -o ConnectTimeout=10 \
                               -o BatchMode=yes \
                               -i ${WORKSPACE}/ec2-deploy.pem \
                               ubuntu@${EC2_IP} "echo SSH_OK" 2>/dev/null | grep -q SSH_OK; then
                            echo "SSH is ready"
                            break
                        fi
                        echo "SSH attempt $i/20 — waiting 15s..."
                        sleep 15
                    done

                    echo "Waiting for Docker to be installed via user_data..."
                    for i in $(seq 1 30); do
                        RESULT=$(ssh -o StrictHostKeyChecking=no \
                               -o ConnectTimeout=10 \
                               -o BatchMode=yes \
                               -i ${WORKSPACE}/ec2-deploy.pem \
                               ubuntu@${EC2_IP} \
                               "test -f /tmp/user_data_done && docker --version && echo READY" 2>/dev/null || true)
                        if echo "$RESULT" | grep -q READY; then
                            echo "Docker is ready: $RESULT"
                            exit 0
                        fi
                        # Print cloud-init status for debugging
                        ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes \
                            -i ${WORKSPACE}/ec2-deploy.pem ubuntu@${EC2_IP} \
                            "cloud-init status 2>/dev/null || echo 'cloud-init not done'" 2>/dev/null || true
                        echo "Docker attempt $i/30 — waiting 15s..."
                        sleep 15
                    done
                    echo "Docker did not become ready in time"
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
${EC2_IP} ansible_user=ubuntu ansible_ssh_private_key_file=${WORKSPACE}/ec2-deploy.pem ansible_ssh_common_args='-o StrictHostKeyChecking=no'
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
            sh "rm -f ec2_ip.txt ecr_repo.txt ec2-deploy.pem ec2-deploy.pub"
        }
    }
}
