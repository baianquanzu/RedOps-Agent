"""
RedOps Web - Skill API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.skill_registry import get_skill_registry

router = APIRouter()


class SkillExecuteRequest(BaseModel):
    """技能执行请求"""
    skill_name: str
    params: Dict[str, Any] = {}


@router.get("/")
async def list_all_skills():
    """列出所有技能"""
    registry = get_skill_registry()
    return {
        "categories": registry.list_categories(),
        "skills": registry.list_skills()
    }


@router.get("/categories")
async def list_categories():
    """列出技能分类"""
    registry = get_skill_registry()
    return {"categories": registry.list_categories()}


@router.get("/category/{category}")
async def list_skills_by_category(category: str):
    """列出指定分类的技能"""
    registry = get_skill_registry()
    return {
        "category": category,
        "skills": registry.list_skills(category)
    }


@router.get("/{skill_name}")
async def get_skill_info(skill_name: str):
    """获取技能详情"""
    registry = get_skill_registry()
    skill = registry.get_skill(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "schema": skill.get_schema()
    }


@router.post("/execute")
async def execute_skill(request: SkillExecuteRequest):
    """执行技能"""
    registry = get_skill_registry()
    
    result = registry.execute_skill(request.skill_name, request.params)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{skill_name}/execute")
async def execute_skill_by_name(skill_name: str, params: Dict[str, Any] = {}):
    """执行指定技能"""
    registry = get_skill_registry()
    
    result = registry.execute_skill(skill_name, params)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
