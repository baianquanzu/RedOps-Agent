"""
RedOps Web - 扫描API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from app.core.manager import ScanManager

router = APIRouter()

# 扫描管理器实例
scan_manager = ScanManager()


class ScanRequest(BaseModel):
    """扫描请求"""
    targets: List[str]
    scan_type: str  # "nuclei", "poc", "all"
    options: Optional[Dict[str, Any]] = {}


class ScanResponse(BaseModel):
    """扫描响应"""
    task_ids: List[str]
    status: str
    message: str


class ScanResult(BaseModel):
    """扫描结果"""
    task_id: str
    status: str
    results: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]


@router.post("/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """开始扫描"""
    if not request.targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if request.scan_type not in ["nuclei", "poc", "all"]:
        raise HTTPException(status_code=400, detail="Invalid scan type")
    
    # 创建批量任务
    task_ids = []
    
    for target in request.targets:
        if request.scan_type == "nuclei" or request.scan_type == "all":
            task_id = scan_manager.create_task(target, "nuclei", request.options)
            task_ids.append(task_id)
            
            # 后台运行Nuclei扫描
            background_tasks.add_task(
                scan_manager.run_nuclei_scan,
                task_id,
                target,
                request.options
            )
        
        if request.scan_type == "poc" or request.scan_type == "all":
            task_id = scan_manager.create_task(target, "poc", request.options)
            task_ids.append(task_id)
            
            # 后台运行POC扫描
            background_tasks.add_task(
                scan_manager.run_poc_scan,
                task_id,
                target
            )
    
    return ScanResponse(
        task_ids=task_ids,
        status="started",
        message=f"Created {len(task_ids)} scan tasks"
    )


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(status: Optional[str] = None):
    """列出所有扫描任务"""
    tasks = scan_manager.get_all_tasks()
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    return tasks


@router.get("/task/{task_id}", response_model=ScanResult)
async def get_task_result(task_id: str):
    """获取任务结果"""
    task = scan_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ScanResult(
        task_id=task.task_id,
        status=task.status,
        results=task.results,
        logs=task.logs
    )


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if scan_manager.delete_task(task_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/clear")
async def clear_completed_tasks():
    """清除已完成任务"""
    scan_manager.clear_completed()
    return {"status": "cleared"}


@router.get("/active")
async def get_active_scans():
    """获取活跃扫描"""
    return {
        "active_count": scan_manager.get_active_count(),
        "targets": scan_manager.targets
    }


@router.get("/templates")
async def list_nuclei_templates():
    """列出Nuclei模板"""
    # 返回内置模板列表
    return {
        "templates": [
            {"id": "cve", "name": "CVE漏洞", "severity": "critical"},
            {"id": "vulnerability", "name": "通用漏洞", "severity": "high"},
            {"id": "exposed-panels", "name": "暴露面板", "severity": "medium"},
            {"id": "exposed-files", "name": "敏感文件", "severity": "high"},
            {"id": "tech-detect", "name": "技术检测", "severity": "info"},
            {"id": "dns", "name": "DNS检测", "severity": "low"},
            {"id": "fuzzing", "name": "模糊测试", "severity": "medium"}
        ],
        "severities": ["critical", "high", "medium", "low", "info"]
    }
