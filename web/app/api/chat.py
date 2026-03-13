"""
RedOps Web - 聊天API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import re

from app.core import get_llm_agent, is_llm_ready, get_memory_system

router = APIRouter()

sessions: Dict[str, Dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    target: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    actions: Optional[List[Dict]] = None


def extract_intent(message: str) -> Dict:
    message_lower = message.lower()
    scan_types = []
    targets = []
    
    if "nuclei" in message_lower or "漏洞" in message:
        scan_types.append("nuclei")
    if "poc" in message_lower or "验证" in message:
        scan_types.append("poc")
    if "fofa" in message_lower or "搜索" in message:
        scan_types.append("fofa")
    if "端口" in message or "scan" in message_lower:
        scan_types.append("port")
    
    urls = re.findall(r'https?://[^\s]+', message)
    targets.extend(urls)
    domains = re.findall(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', message)
    targets.extend(domains)
    
    return {"scan_types": scan_types, "targets": list(set(targets)), "intent": "scan" if scan_types else "chat"}


def generate_response(message: str) -> Dict:
    intent = extract_intent(message)
    
    if intent["intent"] == "scan" and intent["targets"]:
        response = f"好的，我将为您扫描以下目标：\n"
        for target in intent["targets"]:
            response += f"- {target}\n"
        response += "\n现在开始扫描..."
        return {"message": response, "actions": [{"type": "create_scan", "targets": intent["targets"], "scan_types": intent["scan_types"]}]}
    elif intent["intent"] == "scan":
        return {"message": "请告诉我您要测试的目标，可以是URL、域名或IP地址。您也可以指定扫描类型如Nuclei漏洞扫描、POC验证等。"}
    else:
        return {"message": "您好！我是RedOps智能渗透测试助手。我可以帮您：\n\n1. 漏洞扫描 - Nuclei自动化检测\n2. POC验证 - 自定义漏洞验证\n3. 资产搜索 - FOFA同类网站搜索\n4. 端口扫描 - 目标端口检测\n\n请告诉我您的测试需求。"}


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in sessions:
        sessions[session_id] = {"messages": [], "created_at": datetime.now().isoformat(), "target": request.target}
    
    sessions[session_id]["messages"].append({"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()})
    
    if is_llm_ready():
        agent = get_llm_agent()
        result = agent.chat(session_id, request.message)
        if result.get("success"):
            response_msg = result["message"]
        else:
            response = generate_response(request.message)
            response_msg = response["message"]
    else:
        response = generate_response(request.message)
        response_msg = response["message"]
    
    sessions[session_id]["messages"].append({"role": "assistant", "content": response_msg, "timestamp": datetime.now().isoformat()})
    
    return ChatResponse(message=response_msg, session_id=session_id, actions=None)


@router.get("/sessions")
async def list_sessions():
    return [{"session_id": sid, "created_at": s["created_at"], "message_count": len(s["messages"])} for sid, s in sessions.items()]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted"}
    return {"error": "Session not found"}
