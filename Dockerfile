# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 复制示例环境配置文件（如果不存在.env）
RUN if [ ! -f .env ]; then cp env.example .env || echo "No env.example found"; fi

# 暴露端口
EXPOSE 8000

# 启动命令（使用uvicorn，支持热重载可选）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 