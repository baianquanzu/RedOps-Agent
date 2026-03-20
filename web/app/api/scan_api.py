"""
RedOps - 渗透测试扫描API
支持实时推送扫描进度
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import os

router = APIRouter(tags=["渗透测试"])

scan_tasks: Dict[str, Dict] = {}
active_connections: List[WebSocket] = []


class ScanRequest(BaseModel):
    target: str
    config: Optional[Dict[str, Any]] = None


@router.post("/start")
async def start_scan(request: ScanRequest):
    """启动渗透测试扫描"""
    from web.app.core.executor import get_executor
    from web.app.core.orchestrator import get_orchestrator
    
    executor = get_executor()
    workspace = "/tmp/redops_scan"
    os.makedirs(workspace, exist_ok=True)
    
    orchestrator = get_orchestrator(executor, workspace)
    
    task_id = f"scan_{len(scan_tasks)}"
    scan_tasks[task_id] = {
        "target": request.target,
        "status": "running",
        "config": request.config or {},
        "orchestrator": orchestrator
    }
    
    async def run_scan():
        async def send_progress(level: str, message: str):
            progress = 0
            phases = {"1/9": 11, "2/9": 22, "3/9": 33, "4/9": 44, "5/9": 55, "6/9": 66, "7/9": 77, "8/9": 88, "9/9": 95}
            for k, v in phases.items():
                if k in message:
                    progress = v
                    break
            if "完成" in message:
                progress = 100
            
            for ws in active_connections:
                try:
                    await ws.send_json({
                        "type": "scan_progress",
                        "task_id": task_id,
                        "level": level,
                        "message": message,
                        "progress": progress
                    })
                except:
                    pass
        
        orchestrator.set_callback(send_progress)
        result = await orchestrator.run_full_scan(request.target, request.config or {})
        scan_tasks[task_id]["status"] = "completed" if result["success"] else "failed"
        scan_tasks[task_id]["results"] = result.get("results", {})
        
        for ws in active_connections:
            try:
                await ws.send_json({
                    "type": "scan_complete",
                    "task_id": task_id,
                    "success": result["success"]
                })
            except:
                pass
    
    asyncio.create_task(run_scan())
    
    return {"success": True, "task_id": task_id, "message": "扫描已启动，请连接WebSocket监听进度"}


@router.get("/status/{task_id}")
async def get_scan_status(task_id: str):
    if task_id not in scan_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return scan_tasks[task_id]


@router.get("/results/{task_id}")
async def get_scan_results(task_id: str):
    if task_id not in scan_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return scan_tasks[task_id].get("results", {})


@router.websocket("/ws")
async def scan_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        if websocket in active_connections:
            active_connections.remove(websocket)
