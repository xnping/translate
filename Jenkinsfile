pipeline {
    agent any

    environment {
        DEPLOY_HOST = '45.204.6.32'
        DEPLOY_USER = 'root'
        PROJECT_PATH = '/home/translation-api'
        PATH = "/usr/local/bin:/usr/bin:/bin:${env.PATH}"
    }

    stages {
        stage('部署') {
            steps {
                echo '开始部署...'

                withCredentials([usernamePassword(credentialsId: 'server-password', usernameVariable: 'SERVER_USER', passwordVariable: 'SERVER_PASS')]) {
                    sh '''
                        # 安装sshpass（如果没有）
                        which sshpass || (apt-get update && apt-get install -y sshpass) || yum install -y sshpass || true

                        # 创建目录
                        sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$DEPLOY_HOST "mkdir -p $PROJECT_PATH"

                        # 创建临时压缩包
                        tar -czf deploy.tar.gz --exclude='.git' --exclude='.venv' --exclude='__pycache__' .

                        # 上传压缩包
                        sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no deploy.tar.gz $SERVER_USER@$DEPLOY_HOST:$PROJECT_PATH/

                        # 解压并部署
                        sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$DEPLOY_HOST "
                            cd $PROJECT_PATH
                            tar -xzf deploy.tar.gz
                            rm -f deploy.tar.gz
                            python3 -m venv venv || true
                            source venv/bin/activate
                            pip install -r requirements.txt
                            pkill -f 'python.*main.py' || true
                            nohup python main.py > app.log 2>&1 &
                            echo '应用已启动'
                        "

                        # 清理本地文件
                        rm -f deploy.tar.gz
                    '''
                }

                echo '部署完成！'
            }
        }
    }
}
