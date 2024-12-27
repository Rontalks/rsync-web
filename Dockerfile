FROM python:3.9-slim

# 设置pip源为国内源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 设置apt源为国内源
RUN echo "deb https://mirrors.ustc.edu.cn/debian/ bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ bullseye-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list

# 安装rsync和其他必要工具
RUN apt-get update && apt-get install -y rsync locales tzdata

# 设置locale
RUN locale-gen zh_CN.UTF-8
ENV LANG zh_CN.UTF-8
ENV LANGUAGE zh_CN:zh
ENV LC_ALL zh_CN.UTF-8

# 设置默认时区为Asia/Shanghai
ENV TZ=Asia/Shanghai

WORKDIR /app

# 设置pip安装超时时间
ENV PIP_DEFAULT_TIMEOUT=100

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 获取实际的挂载点路径\n\
HOME_PATH=$(readlink -f /home)\n\
DATA_PATH=$(readlink -f /data)\n\
\n\
# 将挂载点信息写入配置文件\n\
echo "{\n\
  \"/home\": \"$HOME_PATH\",\n\
  \"/data\": \"$DATA_PATH\"\n\
}" > /app/mount_points.json\n\
\n\
# 启动应用\n\
python app.py' > /app/start.sh && \
chmod +x /app/start.sh

# 创建非root用户
RUN useradd -u 1000 -m rsyncuser && \
    chown -R rsyncuser:rsyncuser /app

USER rsyncuser

CMD ["/app/start.sh"] 