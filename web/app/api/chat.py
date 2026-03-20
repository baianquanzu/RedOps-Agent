"""
RedOps Web - 聊天API V2
像OpenClaw一样直接执行命令，直接给答案
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import re
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app.core import llm_agent
from web.app.core.executor import get_executor

router = APIRouter()

sessions: Dict[str, Dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    target: Optional[str] = None
    auto_execute: bool = True  # 默认自动执行命令


class ChatResponse(BaseModel):
    message: str
    session_id: str
    actions: Optional[List[Dict]] = None
    executed: Optional[bool] = None
    commands: Optional[List[str]] = None


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [], 
            "created_at": datetime.now().isoformat(), 
            "target": request.target
        }
    
    sessions[session_id]["messages"].append({
        "role": "user", 
        "content": request.message, 
        "timestamp": datetime.now().isoformat()
    })
    
    # 直接调用LLM处理所有输入
    if llm_agent.is_llm_ready():
        agent = llm_agent.get_llm_agent()
        
        # 注入执行器
        if not agent.executor:
            agent.set_executor(get_executor())
        
        # 使用smart_chat - 像OpenClaw一样直接处理
        try:
            result = agent.smart_chat(session_id, request.message)
            
            if result.get("success"):
                response_msg = result.get("message", "执行完成")
                executed = result.get("executed", False)
                commands = result.get("commands", [])
            else:
                response_msg = f"执行出错: {result.get('error', '未知错误')}"
                executed = False
                commands = []
        except Exception as e:
            response_msg = f"处理出错: {str(e)}"
            executed = False
            commands = []
    else:
        # LLM未配置，使用本地智能处理
        response_msg, executed, commands = local_execute(request.message)
    
    sessions[session_id]["messages"].append({
        "role": "assistant", 
        "content": response_msg, 
        "timestamp": datetime.now().isoformat()
    })
    
    return ChatResponse(
        message=response_msg, 
        session_id=session_id, 
        actions=None,
        executed=executed,
        commands=commands
    )


def local_execute(message: str) -> tuple:
    """
    本地执行命令（不调用LLM时的fallback）
    """
    msg_lower = message.lower()
    commands = []
    results = []
    executor = get_executor()
    
    # 端口扫描
    if any(k in msg_lower for k in ["端口", "扫描端口", "开放端口", "port"]):
        target = extract_target(message)
        cmd = f"nmap -sV -p 1-1000 {target}"
        commands.append(cmd)
        result = executor.execute(cmd, timeout=60)
        if result.get("success"):
            output = result.get("stdout", "")
            if "open" in output.lower():
                ports = re.findall(r'(\d+)/open', output)
                results.append(f"发现开放端口: {', '.join(ports)}" if ports else "未发现开放端口")
            else:
                results.append("端口扫描完成")
        else:
            results.append(f"执行失败: {result.get('error', '')}")
    
    # 漏洞扫描
    elif any(k in msg_lower for k in ["漏洞", "漏扫", "vulnerability"]):
        target = extract_target(message)
        cmd = f"nuclei -u {target} -severity critical,high,medium -silent"
        commands.append(cmd)
        result = executor.execute(cmd, timeout=120)
        if result.get("success"):
            output = result.get("stdout", "")
            count = len(output.split('\n')) if output else 0
            if count > 0:
                results.append(f"发现 {count} 个漏洞")
                # 列出关键漏洞
                for line in output.split('\n')[:5]:
                    if line.strip():
                        results.append(f"  - {line[:100]}")
            else:
                results.append("未发现漏洞")
        else:
            results.append(f"执行失败: {result.get('error', '')}")
    
    # 目录扫描
    elif any(k in msg_lower for k in ["目录", "路径", "directory"]):
        target = extract_target(message)
        cmd = f"nuclei -u {target} -tags directory -silent"
        commands.append(cmd)
        result = executor.execute(cmd, timeout=60)
        if result.get("success"):
            output = result.get("stdout", "")
            if output:
                results.append("发现目录:")
                for line in output.split('\n')[:5]:
                    if line.strip():
                        results.append(f"  - {line[:80]}")
            else:
                results.append("未发现敏感目录")
    
    # ping检测
    elif any(k in msg_lower for k in ["ping", "存活", "延迟"]):
        target = extract_target(message)
        cmd = f"ping -c 4 {target}"
        commands.append(cmd)
        result = executor.execute(cmd, timeout=10)
        if result.get("success"):
            output = result.get("stdout", "")
            # 提取延迟
            avg_match = re.search(r'average = ([\d.]+)', output)
            if avg_match:
                results.append(f"目标存活，延迟: {avg_match.group(1)} ms")
            else:
                results.append("目标存活")
        else:
            results.append("目标不可达")
    
    # curl检测 - 使用-L跟随重定向
    elif any(k in msg_lower for k in ["curl", "http", "web", "网站", "检查网站", "测试网站"]):
        target = extract_target(message)
        if not target.startswith("http"):
            target = f"http://{target}"
        cmd = f"curl -sIL {target}"  # -L跟随重定向, -s静默, -I只获取头
        commands.append(cmd)
        result = executor.execute(cmd, timeout=15)
        if result.get("success"):
            output = result.get("stdout", "")
            # 提取最终状态码
            status_matches = re.findall(r'HTTP/[\d\.]+ (\d+)', output)
            if status_matches:
                final_status = status_matches[-1]  # 最后一个是最终状态
                results.append(f"HTTP状态: {final_status}")
                if final_status == "200":
                    results.append("✅ 网站可正常访问")
                elif final_status == "301":
                    results.append("↪️ 永久重定向")
                elif final_status == "302":
                    results.append("↪️ 临时重定向")
                elif final_status == "404":
                    results.append("❌ 页面不存在")
                elif final_status == "500":
                    results.append("❌ 服务器内部错误")
            # 提取server
            server_match = re.search(r'Server: (.+)', output, re.I)
            if server_match:
                results.append(f"🖥️ 服务器: {server_match.group(1).strip()}")
            # 提取Content-Type
            ct_match = re.search(r'Content-Type: (.+)', output, re.I)
            if ct_match:
                results.append(f"📄 类型: {ct_match.group(1).strip()}")
        else:
            results.append(f"请求失败: {result.get('error', '')}")
    
    # whois查询
    elif "whois" in msg_lower:
        target = extract_target(message)
        cmd = f"whois {target}"
        commands.append(cmd)
        result = executor.execute(cmd, timeout=15)
        if result.get("success"):
            output = result.get("stdout", "")
            # 提取关键信息
            for field in ["Registrar", "Creation Date", "Expiry Date", "Name Server"]:
                match = re.search(rf'{field}:?\s*(.+)', output, re.IGNORECASE)
                if match:
                    results.append(f"{field}: {match.group(1).strip()}")
    
    # 帮助
    else:
        results.append("""我可以直接执行以下命令：
• 端口扫描 - "扫描 example.com 的端口"
• 漏洞扫描 - "扫描漏洞" 或 "漏扫"
• 目录扫描 - "扫描目录"
• HTTP检测 - "检查网站" 或 "curl"
• 存活检测 - "ping" 或 "检测存活"
• WHOIS查询 - "whois xxx.com"

直接告诉我做什么，我立即执行！""")
    
    message = '\n'.join(results) if results else "好的，还需要做什么？"
    executed = len(commands) > 0
    
    return message, executed, commands


# ==================== 智能渗透测试执行引擎 ====================

def smart_analyze_intent(message: str) -> dict:
    """智能分析用户意图"""
    msg_lower = message.lower()
    target = extract_target(message)
    
    intents = []
    
    # 端口扫描
    if any(k in msg_lower for k in ["端口", "开放端口", "port", "扫端口", "端口扫描"]):
        intents.append({"type": "port_scan", "cmd": f"nmap -sV -p 1-1000 {target}"})
    
    # 漏洞扫描
    if any(k in msg_lower for k in ["漏洞", "漏扫", "vulnerability", "vuln", "扫描漏洞"]):
        intents.append({"type": "vuln_scan", "cmd": f"nuclei -u {target} -severity critical,high,medium -silent"})
    
    # 目录扫描
    if any(k in msg_lower for k in ["目录", "路径", "directory", "dir", "敏感目录"]):
        intents.append({"type": "dir_scan", "cmd": f"dirb {target}"})
    
    # HTTP检测
    if any(k in msg_lower for k in ["curl", "http", "web", "网站", "检查网站", "状态码"]):
        intents.append({"type": "web_check", "cmd": f"curl -I {target}"})
    
    # 存活检测
    if any(k in msg_lower for k in ["ping", "存活", "延迟", "在线"]):
        intents.append({"type": "ping_check", "cmd": f"ping -c 4 {target}"})
    
    # WHOIS
    if any(k in msg_lower for k in ["whois", "域名信息", "注册信息"]):
        intents.append({"type": "whois", "cmd": f"whois {target}"})
    
    # 全面检测
    if any(k in msg_lower for k in ["全面", "完整", "体检", "测试", "看看"]):
        if target:
            if "." in target and not target.replace(".", "").isdigit():
                intents.append({"type": "web_test", "cmd": f"curl -I {target}"})
            else:
                intents.append({"type": "ip_test", "cmd": f"nmap -sV -p 1-1000 {target}"})
    
    return {"intents": intents, "target": target}


def smart_local_execute(message: str) -> tuple:
    """智能本地执行 - 不需要LLM API"""
    msg_lower = message.lower()
    executor = get_executor()
    
    # 分析意图
    analysis = smart_analyze_intent(message)
    intents = analysis["intents"]
    target = analysis["target"]
    
    # ===== 智能回复各种问题 =====
    
    # 问候语
    if any(k in msg_lower for k in ["你好", "hello", "hi", "您好", "在吗"]):
        return "你好！我是RedOps，你的渗透测试助手。\n\n直接告诉我目标，我可以帮你：\n• 端口扫描  • 漏洞检测  • 目录扫描\n• HTTP检测  • 存活检测  • WHOIS查询\n\n例如：\"测试一下 www.example.com\"", False, []
    
    # 询问能做什么
    if any(k in msg_lower for k in ["你能做什么", "功能", "有什么用", "帮助", "help", "menu"]):
        return """🤖 RedOps 渗透测试助手

我可以帮你完成以下任务：

【信息收集】
• 端口扫描 - "扫描 example.com 的端口"
• 存活检测 - "ping example.com"
• HTTP检测 - "检查网站 example.com"
• WHOIS查询 - "whois example.com"

【漏洞扫描】
• 漏洞扫描 - "扫描漏洞 example.com"
• 目录扫描 - "扫描目录 example.com"

【使用方式】
直接说目标，例如：
• "测试 www.example.com"
• "扫描 192.168.1.1"
• "检测这个网站有没有漏洞"

我立即执行！""", False, []
    
    # 询问结果/什么意思
    if any(k in msg_lower for k in ["什么意思", "什么意思", "为什么", "why", "what"]):
        if target:
            return f"你刚才测试的是: {target}\n\n想做什么操作？\n• 继续扫描端口\n• 检测漏洞\n• 检查网站详情", False, []
        else:
            return "你可以让我帮你测试网站或服务器。\n\n直接说目标，例如：\"测试 www.example.com\"", False, []
    
    # 感谢
    if any(k in msg_lower for k in ["谢谢", "感谢", "thx", "thanks"]):
        return "不客气！有问题随时叫我。", False, []
    
    # ===== 目标处理 =====
    
    # 没有目标，显示功能列表
    if not target:
        return """你可以直接告诉我目标，我会自动测试！

例如：
• "测试 www.example.com"
• "扫描 192.168.1.1 的端口"
• "检测漏洞"

直接说就行！""", False, []
    
    # 有目标但没有明确意图 - 自动执行基本检测
    if not intents:
        # 自动执行基本检测
        results = [f"🎯 目标: {target}", ""]
        commands_exec = []
        
        # 1. HTTP检测
        if "." in target:
            cmd = f"curl -sIL http://{target}"
            commands_exec.append(cmd)
            result = executor.execute(cmd, timeout=15)
            if result.get("success"):
                output = result.get("stdout", "")
                status = re.search(r'HTTP/[\d\.]+ (\d+)', output)
                server = re.search(r'Server: (.+)', output, re.I)
                if status:
                    results.append(f"HTTP状态: {status.group(1)}")
                if server:
                    results.append(f"服务器: {server.group(1).strip()}")
        
        # 2. 端口扫描(快速)
        cmd = f"nmap -F {target}"
        commands_exec.append(cmd)
        result = executor.execute(cmd, timeout=30)
        if result.get("success"):
            output = result.get("stdout", "")
            ports = re.findall(r'(\d+)/open', output)
            if ports:
                results.append(f"开放端口: {', '.join(ports[:10])}")
        
        return "\n".join(results), True, commands_exec
    
    # ===== 有明确意图，执行命令 =====
    
    # 执行命令
    commands_exec = []
    results = []
    
    for intent in intents:
        cmd = intent.get("cmd", "")
        if not cmd or "{target}" in cmd:
            continue
            
        commands_exec.append(cmd)
        result = executor.execute(cmd, timeout=60)
        
        output = result.get("stdout", "")
        
        if result.get("success"):
            # 分析结果
            if "nmap" in cmd:
                if "open" in output.lower():
                    ports = re.findall(r'(\d+)/open', output)
                    svcs = re.findall(r'(\d+)/open\s+(\S+)', output)
                    if ports:
                        results.append(f"开放端口: {', '.join(set(ports))}")
                        if svcs:
                            for p, s in svcs[:5]:
                                results.append(f"  端口{p}: {s}")
                else:
                    results.append("未发现开放端口")
            
            elif "nuclei" in cmd:
                critical = len(re.findall(r'\[critical\]', output, re.I))
                high = len(re.findall(r'\[high\]', output, re.I))
                medium = len(re.findall(r'\[medium\]', output, re.I))
                total = critical + high + medium
                if total > 0:
                    results.append(f"发现漏洞: 严重{critical}个, 高危{high}个, 中危{medium}个")
                else:
                    results.append("未发现漏洞")
            
            elif "curl" in cmd:
                status = re.search(r'HTTP/[\d\.]+ (\d+)', output)
                server = re.search(r'Server: (.+)', output, re.I)
                if status:
                    results.append(f"HTTP状态: {status.group(1)}")
                if server:
                    results.append(f"服务器: {server.group(1).strip()}")
            
            elif "ping" in cmd:
                if "ttl" in output.lower():
                    results.append("目标存活")
                    times = re.findall(r'time[=<]?(\d+\.?\d*)\s*ms', output, re.I)
                    if times:
                        avg = sum(float(t) for t in times) / len(times)
                        results.append(f"延迟: {avg:.1f}ms")
                else:
                    results.append("目标不可达")
            
            elif "whois" in cmd:
                for field in ["Registrar", "Creation Date", "Expiry Date"]:
                    match = re.search(rf'{field}:? (.+)', output, re.I)
                    if match:
                        results.append(f"{field}: {match.group(1).strip()[:50]}")
        else:
            error = result.get("error", "")
            if "not found" in error.lower() or "not recognized" in error.lower():
                tool = cmd.split()[0]
                results.append(f"工具 '{tool}' 不存在")
            else:
                results.append(f"执行失败: {error[:50]}")
    
    if not commands_exec:
        return f"目标: {target}\n请告诉我具体要做什么", False, []
    
    msg = "\n".join(results) if results else "执行完成"
    return msg, True, commands_exec


def extract_target(message: str) -> str:
    """提取目标 - 智能提取URL/IP/域名"""
    # URL - 提取域名部分
    url_match = re.search(r'https?://([^/\s]+)', message)
    if url_match:
        domain = url_match.group(1)
        # 去掉端口
        domain = domain.split(':')[0]
        return domain.rstrip('/')
    
    # IP
    ip_match = re.search(r'(\d{1,3}\.){3}\d{1,3}', message)
    if ip_match:
        return ip_match.group(0)
    
    # 域名
    domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}', message)
    if domain_match:
        return domain_match.group(0)
    
    return ""


@router.get("/sessions")
async def list_sessions():
    return [
        {
            "session_id": sid, 
            "created_at": s["created_at"], 
            "message_count": len(s["messages"])
        } 
        for sid, s in sessions.items()
    ]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted"}
    return {"error": "Session not found"}
