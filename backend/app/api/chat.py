"""
RedOps Web - 智能聊天API
集成LLM和记忆系统
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import uuid
import os

from app.core import get_llm_agent, is_llm_ready, get_memory_system

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    target: Optional[str] = None  # 当前测试目标
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    session_id: str
    actions: Optional[List[Dict[str, Any]]] = None
    scan_results: Optional[Dict[str, Any]] = None
    thinking: Optional[str] = None  # 思考过程


class AutonomousRequest(BaseModel):
    """自主测试请求"""
    target: str
    goal: str  # 测试目标
    session_id: Optional[str] = None
    max_iterations: int = 10


# 会话存储
sessions: Dict[str, Dict[str, Any]] = {}


def extract_intent(message: str) -> Dict[str, Any]:
    """从消息中提取意图"""
    message_lower = message.lower()
    
    # 检测扫描意图
    scan_types = []
    targets = []
    
    if "nuclei" in message_lower or "漏洞扫描" in message or "漏洞检测" in message:
        scan_types.append("nuclei")
    
    if "poc" in message_lower or "验证" in message or " poc" in message_lower:
        scan_types.append("poc")
    
    if "fofa" in message_lower or "搜索" in message or "同类" in message:
        scan_types.append("fofa")
    
    if "端口" in message or "port" in message_lower or "扫描" in message:
        scan_types.append("port")
    
    if "越权" in message or "idor" in message_lower:
        scan_types.append("idor")
    
    if "js" in message_lower or "逆向" in message or "javascript" in message_lower:
        scan_types.append("js_reverse")
    
    # 提取目标
    import re
    # 匹配URL
    urls = re.findall(r'https?://[^\s]+', message)
    targets.extend(urls)
    
    # 匹配域名
    domains = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', message)
    targets.extend(domains)
    
    # 匹配IP地址
    ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', message)
    targets.extend(ips)
    
    return {
        "scan_types": scan_types,
        "targets": list(set(targets)),
        "intent": "scan" if scan_types else "chat"
    }


async def generate_llm_response(message: str, session_id: str, target: str = None) -> Dict[str, Any]:
    """使用LLM生成智能响应"""
    agent = get_llm_agent()
    memory = get_memory_system()
    
    if not agent or not is_llm_ready():
        return {"error": "LLM未初始化", "message": "请先在配置中设置API Key"}
    
    # 获取上下文
    context = memory.get_context_for_session(session_id)
    
    # 构建prompt
    prompt = message
    if context:
        prompt = f"{context}\n\n用户问题: {message}"
    if target:
        prompt = f"当前测试目标: {target}\n\n{prompt}"
    
    # 调用LLM
    result = agent.chat(session_id, prompt)
    
    if result.get("success"):
        # 保存到记忆
        memory.add_memory(
            content=f"用户: {message}",
            memory_type="action",
            target=target,
            session_id=session_id,
            importance=0.5
        )
        memory.add_memory(
            content=f"助手: {result['message'][:200]}",
            memory_type="fact",
            target=target,
            session_id=session_id,
importance=0.5
        )
        
        return {
            "message": result["message"],
            "thinking": None
        }
    else:
        return {"error": result.get("error", "LLM调用失败")}


def generate_response(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """生成响应（非LLM模式）"""
    intent = extract_intent(message)
    
    if intent["intent"] == "scan" and intent["targets"]:
        # 需要执行扫描
        response = f"好的，我了解了您的需求。您希望对以下目标进行扫描：\n"
        for target in intent["targets"]:
            response += f"- {target}\n"
        
        if intent["scan_types"]:
            response += f"\n扫描类型：{', '.join(intent['scan_types'])}\n"
        
        response += "\n我现在开始为您执行扫描，请稍候..."
        
        return {
            "message": response,
            "actions": [
                {
                    "type": "create_scan",
                    "targets": intent["targets"],
                    "scan_types": intent["scan_types"]
                }
            ]
        }
    elif intent["intent"] == "scan" and not intent["targets"]:
        # 需要用户输入目标
        return {
            "message": "好的，我可以帮您进行渗透测试。请告诉我您要测试的目标，可以是：\n- 网站URL（如 https://example.com）\n- 域名（如 example.com）\n- IP地址\n\n您也可以指定扫描类型，如：\n- Nuclei漏洞扫描\n- POC验证\n- FOFA资产搜索\n- 端口扫描"
        }
    else:
        # 普通对话
        return {
            "message": "您好！我是RedOps智能渗透测试助手。我可以帮您：\n\n1. **智能分析** - 分析目标并制定测试计划\n2. **漏洞扫描** - 使用Nuclei进行自动化漏洞检测\n3. **POC验证** - 使用自定义POC进行漏洞验证\n4. **资产搜索** - 使用FOFA搜索同类网站\n5. **端口扫描** - 对目标进行端口扫描\n\n请告诉我您要测试的目标和需求。"
        }


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """处理聊天消息 - 智能助手模式"""
    # 获取或创建会话
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "target": request.target
        }
    
    # 添加用户消息
    sessions[session_id]["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 优先使用LLM
    if is_llm_ready():
        result = await generate_llm_response(request.message, session_id, request.target)
        
        if "error" in result:
            # LLM失败，回退到规则引擎
            response = generate_response(request.message, request.context)
            result = {
                "message": response["message"],
                "actions": response.get("actions"),
                "thinking": None
            }
    else:
        # 使用规则引擎
        response = generate_response(request.message, request.context)
        result = {
            "message": response["message"],
            "actions": response.get("actions"),
            "thinking": None
        }
    
    # 添加助手消息
    sessions[session_id]["messages"].append({
        "role": "assistant",
        "content": result.get("message", ""),
        "timestamp": datetime.now().isoformat()
    })
    
    return ChatResponse(
        message=result.get("message", ""),
        session_id=session_id,
        actions=result.get("actions"),
        scan_results=None,
        thinking=result.get("thinking")
    )


@router.post("/autonomous")
async def autonomous_testing(request: AutonomousRequest):
    """
    自主测试 - 类似OpenClaw的智能测试
    LLM会根据目标自主思考并执行测试
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    if not is_llm_ready():
        raise HTTPException(status_code=400, detail="LLM未初始化，请先配置API Key")
    
    agent = get_llm_agent()
    memory = get_memory_system()
    
    # 创建会话
    agent.create_session(session_id)
    
    # 添加初始上下文
    initial_context = {
        "target": request.target,
        "goal": request.goal,
        "discovered": [],
        "executed": [],
        "status": "started"
    }
    
    # 启动自主思考
    result = agent.autonomous_thinking(
        session_id,
        initial_context,
        max_iterations=request.max_iterations
    )
    
    # 保存发现到记忆
    for finding in result.get("findings", []):
        memory.add_finding(
            target=request.target,
            session_id=session_id,
            finding=finding,
            severity="info"
        )
    
    # 保存测试动作
    for action in result.get("actions_taken", []):
        memory.add_action(
            target=request.target,
            session_id=session_id,
            action=str(action),
            result="已执行"
        )
    
    return {
        "session_id": session_id,
        "target": request.target,
        "goal": request.goal,
        "iterations": result.get("iterations", []),
        "findings": result.get("findings", []),
        "final_plan": result.get("final_plan"),
        "actions_count": len(result.get("actions_taken", []))
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话历史"""
    if session_id in sessions:
        return {
            "session_id": session_id,
            "messages": sessions[session_id]["messages"],
            "created_at": sessions[session_id]["created_at"]
        }
    return {"error": "Session not found"}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        
        # 清除记忆
        memory = get_memory_system()
        memory.clear_session(session_id)
        
        return {"status": "deleted"}
    return {"error": "Session not found"}


@router.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    return [
        {
            "session_id": sid,
            "created_at": session["created_at"],
            "message_count": len(session["messages"]),
            "target": session.get("target")
        }
        for sid, session in sessions.items()
    ]


@router.post("/clear")
async def clear_all_sessions():
    """清除所有会话"""
    sessions.clear()
    return {"status": "cleared"}
