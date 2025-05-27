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

                sshagent(['production-server-key']) {
                    sh '''
                        # 创建目录
                        ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "mkdir -p $PROJECT_PATH"

                        # 上传文件
                        scp -r . $DEPLOY_USER@$DEPLOY_HOST:$PROJECT_PATH/

                        # 安装依赖并启动
                        ssh $DEPLOY_USER@$DEPLOY_HOST "
                            cd $PROJECT_PATH
                            python3 -m venv venv || true
                            source venv/bin/activate
                            pip install -r requirements.txt
                            pkill -f 'python.*main.py' || true
                            nohup python main.py > app.log 2>&1 &
                        "
                    '''
                }

                echo '部署完成！'
            }
        }
    }
}
