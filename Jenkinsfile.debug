pipeline {
    agent any
    
    environment {
        // 项目配置
        PROJECT_NAME = 'translation-api'
        DEPLOY_HOST = '45.204.6.32'
        DEPLOY_USER = 'root'
        PROJECT_PATH = '/home/translation-api'
        
        // 确保PATH包含常用命令路径
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:${env.PATH}"
    }
    
    stages {
        stage('🔍 环境检查') {
            steps {
                echo '正在检查Jenkins环境...'
                
                script {
                    // 基本环境信息
                    sh '''
                        echo "=== 基本环境信息 ==="
                        whoami
                        pwd
                        echo "PATH: $PATH"
                        
                        echo "=== 检查必需命令 ==="
                        which python3 || echo "❌ python3 not found"
                        which git || echo "❌ git not found"
                        which curl || echo "❌ curl not found"
                        which ssh || echo "❌ ssh not found"
                        which scp || echo "❌ scp not found"
                        
                        echo "=== Python版本 ==="
                        python3 --version || echo "❌ Python3 not available"
                        
                        echo "=== 系统信息 ==="
                        uname -a
                        
                        echo "=== 磁盘空间 ==="
                        df -h
                        
                        echo "=== 工作空间内容 ==="
                        ls -la
                    '''
                }
            }
        }
        
        stage('🧪 SSH连接测试') {
            steps {
                echo '正在测试SSH连接...'
                
                script {
                    try {
                        sshagent(['production-server-key']) {
                            sh '''
                                echo "测试SSH连接到 $DEPLOY_HOST..."
                                ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "echo '✅ SSH连接成功'; whoami; pwd"
                            '''
                        }
                    } catch (Exception e) {
                        echo "❌ SSH连接失败: ${e.getMessage()}"
                        echo "请检查:"
                        echo "1. SSH密钥是否正确配置"
                        echo "2. 服务器是否可访问"
                        echo "3. 用户权限是否正确"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
        
        stage('📦 简单部署测试') {
            when {
                expression { currentBuild.result != 'FAILURE' }
            }
            steps {
                echo '正在进行简单部署测试...'
                
                script {
                    try {
                        sshagent(['production-server-key']) {
                            sh '''
                                echo "创建测试目录..."
                                ssh $DEPLOY_USER@$DEPLOY_HOST "mkdir -p /tmp/jenkins-test"
                                
                                echo "上传测试文件..."
                                echo "Jenkins测试文件 - $(date)" > test-file.txt
                                scp test-file.txt $DEPLOY_USER@$DEPLOY_HOST:/tmp/jenkins-test/
                                
                                echo "验证文件上传..."
                                ssh $DEPLOY_USER@$DEPLOY_HOST "cat /tmp/jenkins-test/test-file.txt"
                                
                                echo "清理测试文件..."
                                ssh $DEPLOY_USER@$DEPLOY_HOST "rm -rf /tmp/jenkins-test"
                                rm -f test-file.txt
                                
                                echo "✅ 简单部署测试成功"
                            '''
                        }
                    } catch (Exception e) {
                        echo "❌ 部署测试失败: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
        
        stage('🐍 Python环境测试') {
            when {
                expression { currentBuild.result != 'FAILURE' }
            }
            steps {
                echo '正在测试Python环境...'
                
                script {
                    try {
                        sh '''
                            echo "=== 本地Python环境测试 ==="
                            python3 --version
                            python3 -c "import sys; print('Python路径:', sys.executable)"
                            
                            echo "=== 检查项目文件 ==="
                            if [ -f "requirements.txt" ]; then
                                echo "✅ requirements.txt 存在"
                                echo "依赖列表:"
                                cat requirements.txt
                            else
                                echo "❌ requirements.txt 不存在"
                            fi
                            
                            if [ -f "main.py" ]; then
                                echo "✅ main.py 存在"
                            else
                                echo "❌ main.py 不存在"
                            fi
                            
                            if [ -f "config/languages.yaml" ]; then
                                echo "✅ 语言配置文件存在"
                            else
                                echo "❌ 语言配置文件不存在"
                            fi
                        '''
                        
                        sshagent(['production-server-key']) {
                            sh '''
                                echo "=== 远程Python环境测试 ==="
                                ssh $DEPLOY_USER@$DEPLOY_HOST "
                                    python3 --version || echo '❌ 远程Python3不可用'
                                    which pip3 || echo '❌ 远程pip3不可用'
                                    ls -la $PROJECT_PATH || echo '项目目录不存在，将会创建'
                                "
                            '''
                        }
                    } catch (Exception e) {
                        echo "❌ Python环境测试失败: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo '清理临时文件...'
            sh '''
                rm -f test-file.txt 2>/dev/null || true
            '''
        }
        
        success {
            echo '🎉 调试测试成功！'
            echo '''
            ✅ 所有基础检查都通过了！
            
            📋 检查结果:
            • Jenkins环境: 正常
            • SSH连接: 正常  
            • 文件传输: 正常
            • Python环境: 正常
            
            现在可以尝试完整部署了！
            '''
        }
        
        failure {
            echo '❌ 调试测试失败！'
            echo '''
            请根据上面的错误信息检查:
            1. Jenkins节点环境配置
            2. SSH密钥配置
            3. 服务器连接性
            4. Python环境
            '''
        }
    }
}
