"""
RedOps Web - FastAPI后端主程序
渗透测试Agent Web界面后端
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import uuid

from app.api import chat, targets, scan, config, skills
from app.core.manager import ScanManager

# 创建应用
app = FastAPI(title="RedOps Agent Web", version="2.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 扫描管理器
scan_manager = ScanManager()

# 挂载静态文件
import os
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


class Message(BaseModel):
    """聊天消息"""
    role: str
    content: str
    timestamp: Optional[str] = None


class ScanRequest(BaseModel):
    """扫描请求"""
    targets: List[str]
    scan_type: str  # "nuclei", "poc", "all"
    options: Optional[Dict[str, Any]] = {}


class FOFARequest(BaseModel):
    """FOFA查询请求"""
    query: str
    limit: int = 10


# 前端页面路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回Web界面"""
    import os
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RedOps Agent</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>RedOps Agent Web</h1>
        <p>Frontend not found. Please create frontend/index.html</p>
    </body>
    </html>
    """


# API路由
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(scan.router, prefix="/api/scan", tags=["Scan"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])


# WebSocket连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket实时通信"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理接收到的消息
            message = json.loads(data)
            
            if message.get("type") == "scan_log":
                # 广播扫描日志
                await manager.broadcast(json.dumps({
                    "type": "scan_log",
                    "data": message.get("data")
                }))
            elif message.get("type") == "scan_complete":
                # 扫描完成通知
                await manager.broadcast(json.dumps({
                    "type": "scan_complete",
                    "data": message.get("data")
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "online",
        "version": "2.0.0",
        "active_scans": scan_manager.get_active_count(),
        "targets_count": len(scan_manager.targets)
    }


# FOFA API
from app.integrations.fofa import FOFAClient, FOFA_QUERIES, build_query

fofa_client = FOFAClient()


@app.post("/api/fofa/search")
async def fofa_search(query: str, limit: int = 100, page: int = 1):
    """FOFA搜索"""
    result = fofa_client.search(query, size=limit, page=page)
    return result


@app.get("/api/fofa/queries")
async def get_fofa_queries():
    """获取常用FOFA查询"""
    return FOFA_QUERIES


@app.post("/api/fofa/build")
async def fofa_build_query(keyword: str, **kwargs):
    """构建FOFA查询"""
    query = build_query(keyword, **kwargs)
    return {"query": query}


@app.post("/api/fofa/quick/{query_type}")
async def fofa_quick_search(query_type: str, limit: int = 100):
    """快速FOFA查询"""
    if query_type not in FOFA_QUERIES:
        return {"error": "Unknown query type"}
    
    query = FOFA_QUERIES[query_type]
    result = fofa_client.search(query, size=limit)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
