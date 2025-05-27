pipeline {
    agent any

    stages {
        stage('构建') {
            steps {
                echo '✅ 代码检出成功'
                echo '✅ 项目构建完成'

                script {
                    // 创建部署包
                    sh '''
                        echo "创建部署包..."
                        tar -czf translation-api-$(date +%Y%m%d-%H%M%S).tar.gz \
                            --exclude='.git' \
                            --exclude='.venv' \
                            --exclude='__pycache__' \
                            --exclude='*.pyc' \
                            .

                        echo "部署包创建完成"
                        ls -la *.tar.gz
                    '''
                }

                // 存档构建产物
                archiveArtifacts artifacts: '*.tar.gz', fingerprint: true

                echo '''
                🎉 构建成功！

                📦 部署包已创建并存档

                📋 手动部署步骤：
                1. 下载构建产物 (*.tar.gz)
                2. 上传到服务器 45.204.6.32
                3. 解压到 /home/translation-api/
                4. 运行部署命令：
                   cd /home/translation-api
                   python3 -m venv venv
                   source venv/bin/activate
                   pip install -r requirements.txt
                   python main.py

                🔗 或者使用以下一键部署命令：
                wget http://jenkins-server:8080/job/api/lastSuccessfulBuild/artifact/translation-api-*.tar.gz
                tar -xzf translation-api-*.tar.gz
                cd translation-api
                python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main.py
                '''
            }
        }
    }

    post {
        success {
            echo '🎉 构建成功！部署包已准备就绪'
        }
        failure {
            echo '❌ 构建失败！请检查代码'
        }
        always {
            // 清理临时文件
            sh 'rm -f *.tar.gz || true'
        }
    }
}
