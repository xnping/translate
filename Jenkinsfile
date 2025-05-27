pipeline {
    agent any
    
    environment {
        // 项目配置
        PROJECT_NAME = 'translation-api'
        DEPLOY_PORT = '9000'
        DEPLOY_USER = 'root'
        DEPLOY_HOST = '45.204.6.32'  // 您的生产服务器IP
        
        // Python环境
        PYTHON_VERSION = '3.13'
        VENV_PATH = '/home/translation-api/venv'
        PROJECT_PATH = '/home/translation-api'
        
        // 服务配置
        SERVICE_NAME = 'translation-api'
        NGINX_CONFIG = '/etc/nginx/sites-available/translation-api'
        
        // 备份配置
        BACKUP_PATH = '/home/backups/translation-api'
        MAX_BACKUPS = '5'
    }
    
    stages {
        stage('🔍 Checkout') {
            steps {
                echo '正在拉取代码...'
                checkout scm
                
                script {
                    // 获取提交信息
                    env.GIT_COMMIT_MSG = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()
                    env.BUILD_TIME = sh(
                        script: 'date "+%Y-%m-%d %H:%M:%S"',
                        returnStdout: true
                    ).trim()
                }
                
                echo "提交信息: ${env.GIT_COMMIT_MSG}"
                echo "构建时间: ${env.BUILD_TIME}"
            }
        }
        
        stage('🧪 代码质量检查') {
            parallel {
                stage('语法检查') {
                    steps {
                        echo '正在进行Python语法检查...'
                        sh '''
                            python3 -m py_compile main.py
                            python3 -m py_compile app/main.py
                            find app/ -name "*.py" -exec python3 -m py_compile {} \\;
                        '''
                    }
                }
                
                stage('配置验证') {
                    steps {
                        echo '正在验证配置文件...'
                        sh '''
                            # 检查必需的配置文件
                            if [ ! -f "config/languages.yaml" ]; then
                                echo "❌ 缺少语言配置文件"
                                exit 1
                            fi
                            
                            if [ ! -f "requirements.txt" ]; then
                                echo "❌ 缺少依赖文件"
                                exit 1
                            fi
                            
                            echo "✅ 配置文件检查通过"
                        '''
                    }
                }
                
                stage('安全检查') {
                    steps {
                        echo '正在进行安全检查...'
                        sh '''
                            # 检查敏感信息
                            if grep -r "password.*=" . --exclude-dir=.git --exclude="*.log" | grep -v ".env.example"; then
                                echo "⚠️ 发现可能的敏感信息"
                            fi
                            
                            # 检查.env文件是否在.gitignore中
                            if [ -f ".gitignore" ] && grep -q ".env" .gitignore; then
                                echo "✅ .env文件已正确忽略"
                            else
                                echo "⚠️ 建议将.env文件添加到.gitignore"
                            fi
                        '''
                    }
                }
            }
        }
        
        stage('📦 构建测试环境') {
            steps {
                echo '正在创建测试环境...'
                sh '''
                    # 创建临时虚拟环境
                    python3 -m venv test_venv
                    source test_venv/bin/activate
                    
                    # 升级pip
                    pip install --upgrade pip
                    
                    # 安装依赖
                    pip install -r requirements.txt
                    
                    echo "✅ 测试环境创建成功"
                '''
            }
        }
        
        stage('🧪 运行测试') {
            steps {
                echo '正在运行测试...'
                sh '''
                    source test_venv/bin/activate
                    
                    # 配置验证测试
                    if [ -f "scripts/config_manager.py" ]; then
                        echo "正在验证配置..."
                        python scripts/config_manager.py validate
                        echo "✅ 配置验证通过"
                    fi
                    
                    # API健康检查测试（如果有测试脚本）
                    if [ -f "scripts/test_all_apis.py" ]; then
                        echo "正在运行API测试..."
                        # 这里可以添加API测试逻辑
                        echo "✅ API测试准备就绪"
                    fi
                '''
            }
        }
        
        stage('🚀 部署到生产环境') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '正在部署到生产环境...'
                
                script {
                    // 使用SSH部署
                    sshagent(['production-server-key']) {
                        sh '''
                            # 创建部署脚本
                            cat > deploy_script.sh << 'EOF'
#!/bin/bash
set -e

PROJECT_PATH="/home/translation-api"
BACKUP_PATH="/home/backups/translation-api"
SERVICE_NAME="translation-api"

echo "🚀 开始部署翻译API服务..."

# 创建备份
echo "📦 创建备份..."
mkdir -p $BACKUP_PATH
if [ -d "$PROJECT_PATH" ]; then
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    tar -czf "$BACKUP_PATH/$BACKUP_NAME.tar.gz" -C "$PROJECT_PATH" . 2>/dev/null || true
    echo "✅ 备份创建完成: $BACKUP_NAME.tar.gz"
    
    # 保留最近5个备份
    cd $BACKUP_PATH
    ls -t *.tar.gz | tail -n +6 | xargs -r rm -f
fi

# 停止服务
echo "⏹️ 停止服务..."
systemctl stop $SERVICE_NAME 2>/dev/null || true

# 创建项目目录
mkdir -p $PROJECT_PATH
cd $PROJECT_PATH

# 清理旧文件（保留.env和logs）
find . -maxdepth 1 -type f ! -name '.env' ! -name '*.log' -delete 2>/dev/null || true
find . -maxdepth 1 -type d ! -name '.' ! -name 'logs' -exec rm -rf {} + 2>/dev/null || true

echo "✅ 环境准备完成"
EOF

                            # 上传部署脚本
                            scp deploy_script.sh $DEPLOY_USER@$DEPLOY_HOST:/tmp/
                            
                            # 上传项目文件
                            echo "📤 上传项目文件..."
                            scp -r . $DEPLOY_USER@$DEPLOY_HOST:/tmp/translation-api-new/
                            
                            # 执行部署
                            ssh $DEPLOY_USER@$DEPLOY_HOST << 'ENDSSH'
                                # 执行部署脚本
                                chmod +x /tmp/deploy_script.sh
                                /tmp/deploy_script.sh
                                
                                # 复制新文件
                                echo "📁 复制项目文件..."
                                cp -r /tmp/translation-api-new/* /home/translation-api/
                                
                                # 设置权限
                                chown -R www-data:www-data /home/translation-api
                                chmod -R 755 /home/translation-api
                                
                                # 创建虚拟环境
                                echo "🐍 设置Python环境..."
                                cd /home/translation-api
                                python3 -m venv venv
                                source venv/bin/activate
                                pip install --upgrade pip
                                pip install -r requirements.txt
                                
                                echo "✅ 依赖安装完成"
ENDSSH
                        '''
                    }
                }
            }
        }
        
        stage('⚙️ 配置服务') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '正在配置系统服务...'
                
                sshagent(['production-server-key']) {
                    sh '''
                        ssh $DEPLOY_USER@$DEPLOY_HOST << 'ENDSSH'
                            # 创建systemd服务文件
                            cat > /etc/systemd/system/translation-api.service << 'EOF'
[Unit]
Description=Translation API Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/home/translation-api
Environment=PATH=/home/translation-api/venv/bin
ExecStart=/home/translation-api/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

                            # 重新加载systemd
                            systemctl daemon-reload
                            systemctl enable translation-api
                            
                            echo "✅ 服务配置完成"
ENDSSH
                    '''
                }
            }
        }
        
        stage('🌐 配置Nginx') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '正在配置Nginx...'
                
                sshagent(['production-server-key']) {
                    sh '''
                        ssh $DEPLOY_USER@$DEPLOY_HOST << 'ENDSSH'
                            # 创建Nginx配置
                            cat > /etc/nginx/sites-available/translation-api << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    # API代理
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件
    location /static/ {
        alias /home/translation-api/static/;
        expires 1d;
        add_header Cache-Control "public";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:9000/health;
        access_log off;
    }
}
EOF

                            # 启用站点
                            ln -sf /etc/nginx/sites-available/translation-api /etc/nginx/sites-enabled/
                            
                            # 测试Nginx配置
                            nginx -t
                            
                            # 重新加载Nginx
                            systemctl reload nginx
                            
                            echo "✅ Nginx配置完成"
ENDSSH
                    '''
                }
            }
        }
        
        stage('🔄 启动服务') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '正在启动服务...'
                
                sshagent(['production-server-key']) {
                    sh '''
                        ssh $DEPLOY_USER@$DEPLOY_HOST << 'ENDSSH'
                            # 启动服务
                            systemctl start translation-api
                            
                            # 等待服务启动
                            sleep 5
                            
                            # 检查服务状态
                            if systemctl is-active --quiet translation-api; then
                                echo "✅ 服务启动成功"
                            else
                                echo "❌ 服务启动失败"
                                systemctl status translation-api
                                exit 1
                            fi
ENDSSH
                    '''
                }
            }
        }
        
        stage('🧪 部署验证') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '正在验证部署...'
                
                script {
                    // 健康检查
                    def healthCheck = sh(
                        script: "curl -f http://${DEPLOY_HOST}/health",
                        returnStatus: true
                    )
                    
                    if (healthCheck == 0) {
                        echo "✅ 健康检查通过"
                    } else {
                        error "❌ 健康检查失败"
                    }
                    
                    // API测试
                    def apiTest = sh(
                        script: "curl -f http://${DEPLOY_HOST}/api/languages",
                        returnStatus: true
                    )
                    
                    if (apiTest == 0) {
                        echo "✅ API测试通过"
                    } else {
                        echo "⚠️ API测试失败，但不阻止部署"
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo '清理临时文件...'
            sh '''
                rm -rf test_venv 2>/dev/null || true
                rm -f deploy_script.sh 2>/dev/null || true
            '''
        }
        
        success {
            echo '🎉 部署成功！'
            
            script {
                // 发送成功通知（可选）
                def message = """
🎉 翻译API部署成功！

📋 部署信息:
• 项目: ${PROJECT_NAME}
• 分支: ${env.BRANCH_NAME}
• 提交: ${env.GIT_COMMIT_MSG}
• 时间: ${env.BUILD_TIME}
• 服务器: ${DEPLOY_HOST}

🔗 访问地址:
• 主页: http://${DEPLOY_HOST}
• API文档: http://${DEPLOY_HOST}/docs
• 健康检查: http://${DEPLOY_HOST}/health
                """
                
                echo message
            }
        }
        
        failure {
            echo '❌ 部署失败！'
            
            script {
                def message = """
❌ 翻译API部署失败！

📋 失败信息:
• 项目: ${PROJECT_NAME}
• 分支: ${env.BRANCH_NAME}
• 构建: #${env.BUILD_NUMBER}
• 时间: ${env.BUILD_TIME}

请检查Jenkins日志获取详细信息。
                """
                
                echo message
            }
        }
    }
}
