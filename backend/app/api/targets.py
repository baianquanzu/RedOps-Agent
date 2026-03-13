"""
RedOps Web - 目标管理API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import re

router = APIRouter()


class Target(BaseModel):
    """目标"""
    id: Optional[str] = None
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[str] = None
    last_scan: Optional[str] = None
    status: str = "active"


class TargetGroup(BaseModel):
    """目标组"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    targets: List[str] = []  # target IDs
    created_at: Optional[str] = None


# 存储
targets_db: Dict[str, Target] = {}
target_groups_db: Dict[str, TargetGroup] = {}


def validate_target(url: str) -> bool:
    """验证目标格式"""
    # URL格式
    url_pattern = r'^https?://[^\s]+$'
    # 域名格式
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    # IP格式
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    
    return bool(re.match(url_pattern, url) or re.match(domain_pattern, url) or re.match(ip_pattern, url))


@router.post("/targets", response_model=Target)
async def create_target(target: Target):
    """创建目标"""
    if not validate_target(target.url):
        raise HTTPException(status_code=400, detail="Invalid target format")
    
    target_id = str(uuid.uuid4())
    target.id = target_id
    target.created_at = datetime.now().isoformat()
    
    targets_db[target_id] = target
    return target


@router.get("/targets", response_model=List[Target])
async def list_targets(
    tag: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """列出目标"""
    result = list(targets_db.values())
    
    # 按标签过滤
    if tag:
        result = [t for t in result if tag in t.tags]
    
    # 按状态过滤
    if status:
        result = [t for t in result if t.status == status]
    
    # 搜索
    if search:
        search_lower = search.lower()
        result = [
            t for t in result 
            if search_lower in t.url.lower() or 
               (t.name and search_lower in t.name.lower()) or
               (t.description and search_lower in t.description.lower())
        ]
    
    return result


@router.get("/targets/{target_id}", response_model=Target)
async def get_target(target_id: str):
    """获取目标详情"""
    if target_id not in targets_db:
        raise HTTPException(status_code=404, detail="Target not found")
    return targets_db[target_id]


@router.put("/targets/{target_id}", response_model=Target)
async def update_target(target_id: str, target: Target):
    """更新目标"""
    if target_id not in targets_db:
        raise HTTPException(status_code=404, detail="Target not found")
    
    target.id = target_id
    targets_db[target_id] = target
    return target


@router.delete("/targets/{target_id}")
async def delete_target(target_id: str):
    """删除目标"""
    if target_id not in targets_db:
        raise HTTPException(status_code=404, detail="Target not found")
    
    del targets_db[target_id]
    return {"status": "deleted"}


@router.post("/targets/batch")
async def create_targets_batch(targets: List[Target]):
    """批量创建目标"""
    created = []
    errors = []
    
    for target in targets:
        if not validate_target(target.url):
            errors.append({"url": target.url, "error": "Invalid format"})
            continue
        
        target_id = str(uuid.uuid4())
        target.id = target_id
        target.created_at = datetime.now().isoformat()
        
        targets_db[target_id] = target
        created.append(target)
    
    return {
        "created": created,
        "errors": errors
    }


@router.post("/targets/import")
async def import_targets(
    content: str,  # 文本内容，每行一个目标
    format: str = "auto",  # auto, url, domain, ip
    tags: List[str] = []
):
    """从文本批量导入目标
    
    支持格式：
    - 每行一个目标
    - 可以是URL、域名、IP地址
    - 支持逗号分隔
    - 支持空格分隔
    """
    created = []
    errors = []
    
    # 分割输入
    lines = content.replace(',', '\n').replace(' ', '\n').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    for line in lines:
        # 提取目标
        target_url = line
        
        # 根据格式处理
        if format == "url" and not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        elif format == "auto":
            if not target_url.startswith(('http://', 'https://')):
                # 尝试识别是否为IP
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target_url):
                    target_url = 'http://' + target_url
                else:
                    target_url = 'https://' + target_url
        
        if not validate_target(target_url):
            errors.append({"url": line, "error": "Invalid format"})
            continue
        
        # 创建目标
        target = Target(
            url=target_url,
            tags=tags,
            status="active"
        )
        
        target_id = str(uuid.uuid4())
        target.id = target_id
        target.created_at = datetime.now().isoformat()
        
        targets_db[target_id] = target
        created.append(target)
    
    return {
        "total": len(lines),
        "created": len(created),
        "errors": len(errors),
        "targets": [t.dict() for t in created],
        "error_details": errors
    }


@router.post("/targets/import/file")
async def import_targets_from_file(file_content: str, tags: List[str] = []):
    """从文件内容导入目标"""
    return await import_targets(file_content, format="auto", tags=tags)


@router.get("/targets/export")
async def export_targets(format: str = "txt"):
    """导出目标
    
    format: txt, json, csv
    """
    targets = list(targets_db.values())
    
    if format == "txt":
        content = "\n".join([t.url for t in targets])
        return {
            "format": "txt",
            "content": content,
            "count": len(targets)
        }
    elif format == "json":
        return {
            "format": "json",
            "targets": [t.dict() for t in targets],
            "count": len(targets)
        }
    elif format == "csv":
        lines = ["url,name,description,tags,status"]
        for t in targets:
            tags_str = ",".join(t.tags) if t.tags else ""
            lines.append(f'"{t.url}","{t.name or ""}","{t.description or ""}","{tags_str}","{t.status}"')
        return {
            "format": "csv",
            "content": "\n".join(lines),
            "count": len(targets)
        }
    
    return {"error": "Unsupported format"}


@router.post("/targets/groups/batch")
async def create_targets_group(name: str, targets: List[str], description: str = None):
    """批量创建目标组"""
    group_id = str(uuid.uuid4())
    
    # 验证目标是否存在
    valid_targets = []
    for target_id in targets:
        if target_id in targets_db:
            valid_targets.append(target_id)
    
    group = TargetGroup(
        id=group_id,
        name=name,
        description=description,
        targets=valid_targets,
        created_at=datetime.now().isoformat()
    )
    
    target_groups_db[group_id] = group
    
    return {
        "created": group.dict(),
        "valid_targets": len(valid_targets)
    }


@router.get("/tags")
async def list_tags():
    """列出所有标签"""
    tags = set()
    for target in targets_db.values():
        tags.update(target.tags)
    return {"tags": sorted(list(tags))}


# 目标组管理
@router.post("/groups", response_model=TargetGroup)
async def create_group(group: TargetGroup):
    """创建目标组"""
    group_id = str(uuid.uuid4())
    group.id = group_id
    group.created_at = datetime.now().isoformat()
    
    target_groups_db[group_id] = group
    return group


@router.get("/groups", response_model=List[TargetGroup])
async def list_groups():
    """列出目标组"""
    return list(target_groups_db.values())


@router.get("/groups/{group_id}", response_model=TargetGroup)
async def get_group(group_id: str):
    """获取目标组"""
    if group_id not in target_groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    return target_groups_db[group_id]


@router.delete("/groups/{group_id}")
async def delete_group(group_id: str):
    """删除目标组"""
    if group_id not in target_groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    
    del target_groups_db[group_id]
    return {"status": "deleted"}
