# Rsync Web UI

一个基于Web界面的Rsync同步工具，支持定时同步任务和文件浏览器功能。

## 功能特点

- 📂 可视化的文件浏览器，轻松选择源路径和目标路径
- ⏰ 灵活的定时任务设置
  - 每天定时执行
  - 每周定时执行
  - 每月定时执行
  - 自定义时间间隔执行
- 🔄 支持即时同步操作
- 🗑️ 可选的`--delete`选项，保持目标目录与源目录完全一致
- 📝 支持为同步任务添加备注说明
- 📱 响应式设计，支持移动端访问

## 快速开始

### 使用 Docker Compose 部署

1. 克隆项目到本地：

  ```
  git clone https://github.com/Rontalks/rsync-web.git
  cd rsync-web-ui
  ```

  

2. 修改 `docker-compose.yml` 中的挂载路径：

  ```
  volumes:
  "/your/source/path:/home:ro" # 源路径，只读模式
  "/your/target/path:/data" # 目标路径，读写模式
  ```

  

3. 启动服务：

  ```
  docker-compose up -d
  ```

  

4. 访问 Web 界面：

打开浏览器访问 `http://your-server-ip:8856`

## 配置说明

### 挂载路径

- `/home`: 源文件路径，建议以只读方式挂载
- `/data`: 目标文件路径，需要读写权限

### 环境变量

- `TZ`: 时区设置，默认为 `Asia/Shanghai`
- `LANG`/`LANGUAGE`/`LC_ALL`: 语言设置，默认为中文

## 使用说明

1. 在 Web 界面中，使用文件浏览器选择源路径和目标路径
2. 可选择是否启用 `--delete` 选项
3. 可以设置定时同步：
   - 每天定时
   - 每周定时（指定星期几）
   - 每月定时（指定日期）
   - 间隔执行（自定义分钟或小时）
4. 可以为任务添加备注说明
5. 可以随时手动触发同步
6. 支持编辑和删除已创建的任务

## 技术栈

- 后端：Python Flask
- 前端：原生 JavaScript + HTML + CSS
- 容器化：Docker
- 同步工具：Rsync

## 目录结构
.

├── app/

│ ├── templates/

│ │ └── index.html # Web界面模板

│ ├── app.py # Flask应用主程序

│ └── requirements.txt # Python依赖

├── docker-compose.yml # Docker Compose配置文件

├── Dockerfile # Docker构建文件

└── README.md # 项目说明文档

## 安全说明

- 建议将源路径以只读方式挂载，防止意外修改
- 建议在内网环境使用，如需外网访问请做好安全防护
- 默认使用非 root 用户运行容器

## 注意事项

1. 建议将定时任务的间隔设置为不少于5分钟
2. 首次运行时会自动创建必要的数据目录
3. 任务配置数据保存在容器的 `/app/data` 目录下
4. 修改时区和语言设置可以通过环境变量实现

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[MIT License](LICENSE)