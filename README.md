# RedOps Agent

> ⚠️ **测试版 (v0.1)** - 功能正在持续开发完善中

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux%20|%20Windows%20|%20macOS-green.svg)](https://www.kali.org/)
[![Status](https://img.shields.io/badge/Status-Beta-orange.svg)]()

## ⚠️ 免责声明

**本工具仅供学习和研究使用，请勿用于任何未经授权的渗透测试。**
使用本工具时，请确保遵守当地法律法规，因滥用导致的任何后果由使用者自行承担。

## 当前功能

### ✅ 已实现

| 功能 | 说明 | 状态 |
|------|------|------|
| 对话助手 | 基于LLM的对话交互 | 可用 |
| 终端 | WebShell操作界面 | 可用 |
| 文件管理 | 文件浏览、上传、下载 | 可用 |
| 漏洞扫描 | Nuclei集成 | 基础可用 |
| 渗透工作流 | 9阶段半自动化扫描 | 测试中 |

### 🔧 开发中

| 功能 | 说明 | 进度 |
|------|------|------|
| FOFA集成 | FOFA API资产搜集 | 待测试 |
| 子域名爆破 | Subfinder/Assetfinder集成 | 基础可用 |
| 弱口令检测 | Hydra爆破 | 待完善 |
| 实时进度推送 | WebSocket | 基础可用 |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/baianquanzu/RedOps-Agent.git
cd RedOps-Agent
```

### 2. 安装依赖

**Kali Linux 2024.4+:**
```bash
bash setup_env.sh
```

**Windows/macOS:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 前置工具（可选）

部分功能需要提前安装的工具：
```bash
# Kali自带工具（如果没有）
sudo apt install nmap nuclei curl
```

### 4. 配置LLM

启动后访问 http://localhost:8000 ，进入「系统设置」配置：

| 配置项 | 说明 |
|--------|------|
| API Provider | 选择服务商 (DeepSeek/OpenAI等) |
| API Key | 你的API密钥 |
| API地址 | API端点URL |
| 模型 | 使用的模型名称 |

### 5. 启动服务

```bash
bash start.sh
```

服务启动后访问 **http://localhost:8000**

## 技术架构

```
┌─────────────────────────────────────────┐
│              Web界面 (HTML/JS)           │
├─────────────────────────────────────────┤
│           FastAPI Web后端                │
│  ┌─────────┬──────────┬────────────┐  │
│  │ Chat API│Terminal API│Files API  │  │
│  └─────────┴──────────┴────────────┘  │
├─────────────────────────────────────────┤
│           LLM Agent (LLM集成)           │
├─────────────────────────────────────────┤
│         System Executor (命令执行)        │
└─────────────────────────────────────────┘
```

## 依赖工具

部分功能依赖系统工具，请确保已安装：

| 工具 | 用途 | 安装命令 |
|------|------|---------|
| nmap | 端口扫描 | `sudo apt install nmap` |
| nuclei | 漏洞扫描 | 见官方安装 |
| curl | HTTP请求 | `sudo apt install curl` |
| subfinder | 子域名 | 见官方安装 |
| dirsearch | 目录扫描 | 见官方安装 |
| ffuf | 模糊测试 | `sudo apt install ffuf` |
| hydra | 暴力破解 | `sudo apt install hydra` |

**注意**: 这些工具不是必须安装的，但安装后会获得完整功能体验。

## 项目结构

```
RedOps/
├── web/                    # Web后端
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心模块 (Agent、执行器、编排器)
│   │   └── static/       # 静态文件
│   └── main.py           # 入口文件
├── frontend/              # 前端页面
├── requirements.txt      # Python依赖
├── setup_env.sh          # 环境安装脚本
└── start.sh             # 启动脚本
```

## 系统要求

- Python 3.10+
- Kali Linux 2024.4+ / Windows 10+ / macOS
- 推荐 4GB+ RAM
- 网络连接（用于LLM API调用）

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat/message` | POST | 对话接口 |
| `/api/terminal/exec` | POST | 执行命令 |
| `/api/files/list` | POST | 列出目录 |
| `/api/files/upload` | POST | 上传文件 |
| `/api/files/download` | GET | 下载文件 |
| `/api/recon/start` | POST | 启动扫描 |

## 已知问题

- 渗透工作流部分功能需要手动安装依赖工具
- FOFA API集成尚未完整测试
- 弱口令检测功能待完善
- 实时进度推送偶发延迟

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
