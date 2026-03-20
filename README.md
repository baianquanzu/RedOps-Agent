# RedOps Agent

> 智能渗透测试Agent - 像人类一样思考和行动的自动化测试助手

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux%20|%20Windows%20|%20macOS-green.svg)](https://www.kali.org/)

## 特性

- **智能对话** - 大模型驱动，自然语言交互
- **终端控制** - Web界面直接操作root shell
- **文件管理** - Root权限文件浏览、上传、下载
- **漏洞扫描** - 集成Nuclei、Nmap等扫描工具
- **跨平台** - 支持Kali Linux、Windows、macOS

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/RedOps.git
cd RedOps
```

### 2. 安装依赖

**Kali Linux 2024.4+:**
```bash
bash setup_env.sh
```

**Windows/macOS:**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置LLM

启动后访问 http://localhost:8000 ，进入「系统设置」配置：

| 配置项 | 说明 |
|--------|------|
| API Provider | 选择服务商 (DeepSeek/OpenAI/Anthropic等) |
| API Key | 你的API密钥 |
| API地址 | API端点URL |
| 模型 | 使用的模型名称 |

### 4. 启动服务

```bash
# 方式1：一键启动
bash start.sh

# 方式2：手动启动
source venv/bin/activate
python start_server.py
```

服务启动后访问 **http://localhost:8000**

## 功能模块

### 对话助手
- 自然语言与Agent交互
- 自动分析和执行命令
- 智能结果分析

### 终端
- WebShell操作界面
- Root权限命令执行
- 实时命令输出

### 文件管理
- 完整文件系统浏览
- 文件上传/下载
- 文本编辑器

### 漏洞扫描
- Nmap端口扫描
- Nuclei漏洞扫描
- 自定义扫描任务

## 项目结构

```
RedOps/
├── web/                    # Web后端
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心模块
│   │   └── static/       # 静态文件
│   └── main.py           # 入口文件
├── frontend/              # 前端页面
├── requirements.txt       # Python依赖
├── setup_env.sh         # 环境安装脚本
└── start.sh             # 启动脚本
```

## 系统要求

- Python 3.10+
- Kali Linux 2024.4+ / Windows 10+ / macOS
- 推荐 4GB+ RAM
- 网络连接（用于LLM API调用）

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: 原生HTML/CSS/JavaScript
- **LLM**: OpenAI/DeepSeek兼容API
- **终端**: WebSocket实时交互

## 使用示例

```
用户: 帮我扫描 example.com 的开放端口
Agent: [自动执行端口扫描命令]
      [分析扫描结果]
      [返回: 发现开放端口: 22, 80, 443, 3306]
```

```
用户: 这个网站有没有SQL注入
Agent: [自动进行SQL注入测试]
      [分析测试结果]
      [返回: 未发现SQL注入漏洞 或 发现漏洞位置]
```

## 注意事项

⚠️ **仅用于授权的安全测试**  
请确保您拥有目标系统的合法授权。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
