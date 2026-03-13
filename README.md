# RedOps - 智能渗透测试Agent框架

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge&logo=python" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-orange?style=for-the-badge" alt="Platform">
</p>

<p align="center">
  <strong>RedOps</strong> - 基于LLM的智能渗透测试Agent框架
</p>

---

## 项目简介

RedOps 是一款专为渗透测试行业设计的智能Agent框架，基于大语言模型（LLM）驱动，能够自主完成信息收集、漏洞扫描、渗透测试等工作。框架采用模块化设计，支持多种LLM接入，并提供Web界面和桌面宠物两种交互方式。

本框架适用于安全研究人员、渗透测试工程师、红队队员等安全从业者，可显著提升渗透测试效率。

---

## 功能特点

### 🤖 智能Agent核心

- **LLM驱动**: 支持DeepSeek、OpenAI、Anthropic Claude、阿里云Qwen等多种大语言模型
- **自主决策**: 基于自然语言理解，自动规划渗透测试路径
- **上下文记忆**: 持久化会话上下文，支持多轮对话和任务连续性
- **技能注册**: 动态加载技能模块，可扩展渗透测试能力

### 🛠️ 渗透测试工具集成

- **Nuclei集成**: 调用Nuclei进行漏洞扫描，支持自定义POC
- **FOFA资产搜索**: 集成FOFA接口，快速发现目标资产
- **系统命令执行**: 集成Kali Linux工具链，执行各类渗透测试命令
- **JS逆向分析**: 自动分析页面JavaScript代码，提取敏感信息

### 📊 Web管理界面

- **对话界面**: 通过自然语言与Agent交互，下达渗透测试任务
- **目标管理**: 管理渗透测试目标，支持多目标批量测试
- **技能市场**: 浏览和管理可用的渗透测试技能
- **实时状态**: 监控扫描进度和任务状态
- **报告生成**: 自动生成HTML格式的渗透测试报告

### 🖥️ 桌面宠物

- **黑客少女形象**: 仿天选姬风格的黑客少女桌宠
- **状态反馈**: 实时显示渗透测试进度和结果
- **交互功能**: 支持拖拽、点击等交互操作

---

## 环境要求

### Python环境

- Python 3.10 或更高版本
- 推荐使用虚拟环境（venv）隔离依赖

### 操作系统

- **Kali Linux**: 最佳运行平台，预装大部分渗透测试工具
- **Windows**: 支持，需手动安装相关工具
- **其他Linux发行版**: 部分支持

### 必需工具（Kali Linux）

```bash
# 建议安装的工具
sudo apt update
sudo apt install -y python3-pip python3-venv git curl wget
# Nuclei (漏洞扫描)
sudo apt install nuclei -y
# 其他常用工具
sudo apt install -y nmap sqlmap dirb gobuster
```

### 网络要求

- 能够访问OpenAI API / DeepSeek API / 其他LLM服务
- 能够访问FOFA等资产搜索平台（可选）

---

## 安装配置

### 1. 克隆项目

```bash
git clone https://github.com/baianquanzu/RedOps-Agent.git
cd RedOps-Agent
```

### 2. 创建虚拟环境（推荐）

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置LLM API

编辑 `web/app/core/config.yaml` 或通过Web界面配置：

```yaml
llm:
  provider: "deepseek"  # 可选: deepseek, openai, anthropic, qwen
  api_key: "your-api-key-here"
  base_url: "https://api.deepseek.com/v1"  # 根据提供商调整
  model: "deepseek-chat"
```

### 5. 配置FOFA（可选）

```yaml
fofa:
  email: "your-email@example.com"
  key: "your-fofa-api-key"
```

---

## 快速开始

### 方式一：Windows一键启动

双击运行 `start.bat`，选择启动选项：

```
========================================
       RedOps 渗透测试Agent框架
========================================
请选择启动模式：
1. 启动Web界面 (推荐)
2. 启动桌面宠物
3. 同时启动Web和桌宠
4. 仅安装依赖
5. 退出
```

### 方式二：Kali Linux一键启动

```bash
# 添加执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

### 方式三：手动启动

#### 启动Web服务

```bash
# 进入项目目录
cd RedOps-Agent

# 启动Web服务
cd web
python main.py
```

服务启动后，浏览器访问 http://localhost:8000

#### 启动桌面宠物

```bash
python desktop_pet.py
```

---

## 使用指南

### Web界面使用

1. **访问界面**: 打开浏览器访问 http://localhost:8000
2. **配置API**: 在设置页面配置LLM API密钥
3. **添加目标**: 在目标管理页面添加渗透测试目标
4. **开始测试**: 通过对话界面下达测试任务

### 示例命令

```
"请对 192.168.1.1 进行端口扫描"
"使用Nuclei扫描 example.com 的漏洞"
"查找 example.com 的子域名"
"对目标进行SQL注入测试"
```

### 桌面宠物交互

- **拖拽移动**: 拖动窗口移动桌宠位置
- **右键菜单**: 右键点击显示操作菜单
- **状态显示**: 桌宠表情反映当前任务状态

---

## 项目结构

```
RedOps-Agent/
├── web/                      # Web后端服务
│   ├── main.py             # FastAPI主程序
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   ├── chat.py     # 对话接口
│   │   │   ├── scan.py     # 扫描接口
│   │   │   ├── targets.py  # 目标管理
│   │   │   └── skills.py   # 技能管理
│   │   ├── core/           # 核心模块
│   │   │   ├── llm_agent.py    # LLM智能代理
│   │   │   ├── memory_system.py # 记忆系统
│   │   │   ├── skill_registry.py # 技能注册
│   │   │   └── manager.py   # 任务管理器
│   │   └── integrations/   # 第三方集成
│   │       └── fofa.py      # FOFA集成
│   └── templates/           # HTML模板
├── frontend/                # Web前端
│   └── index.html          # 单页应用
├── desktop_pet.py          # 桌面宠物
├── start.sh                # Kali启动脚本
├── start.bat               # Windows启动脚本
└── requirements.txt        # Python依赖
```

---

## 配置说明

### LLM提供商配置

#### DeepSeek

```yaml
llm:
  provider: "deepseek"
  api_key: "your-deepseek-api-key"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
```

#### OpenAI

```yaml
llm:
  provider: "openai"
  api_key: "your-openai-api-key"
  model: "gpt-4"
```

#### Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  api_key: "your-claude-api-key"
  model: "claude-3-opus-20240229"
```

#### 阿里云Qwen

```yaml
llm:
  provider: "qwen"
  api_key: "your-qwen-api-key"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-plus"
```

### 高级配置

#### 自定义技能

在 `web/app/core/skills/` 目录下添加自定义技能模块。

#### Nuclei模板

项目使用Nuclei官方模板库，支持自定义POC。

---

## 注意事项

⚠️ **免责声明**: 本工具仅供授权的安全测试和渗透测试使用。未经授权使用本工具对他人系统进行渗透测试是违法行为，使用者需自行承担法律责任。

- 请确保在获得授权的情况下使用本工具
- 遵守当地法律法规
- 建议在隔离环境（如虚拟机）中测试使用

---

## 常见问题

### Q: 启动失败提示缺少依赖

```bash
pip install -r requirements.txt
```

### Q: LLM API调用失败

- 检查API密钥是否正确
- 确认网络能够访问API服务
- 查看日志中的具体错误信息

### Q: 桌面宠物显示异常

- 确保已安装tkinter库
- Windows用户可能需要安装ActiveTcl

### Q: Nuclei扫描失败

- 确认Nuclei已正确安装
- 检查目标网络连通性

---

## 技术支持

- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions

---

## 更新日志

### v1.0.0 (2026-03)

- 初始版本发布
- LLM智能代理核心
- Web界面
- 桌面宠物
- Nuclei集成
- FOFA资产搜索

---

## License

MIT License

---

<p align="center">Made with ❤️ by RedOps Team</p>
