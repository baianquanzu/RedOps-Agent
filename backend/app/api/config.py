"""
RedOps Web - 配置管理API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core import init_llm_agent, get_llm_agent, is_llm_ready, get_memory_system

router = APIRouter()


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = "deepseek"  # "deepseek", "openai", "anthropic", "ollama", "zhipu", "minimax"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096


class NucleiConfig(BaseModel):
    """Nuclei配置"""
    severity: List[str] = ["critical", "high", "medium"]
    tags: List[str] = []
    rate_limit: int = 150
    threads: int = 50
    poc_dir: str = "./pocs"


class FOFAConfig(BaseModel):
    """FOFA配置"""
    email: Optional[str] = None
    key: Optional[str] = None
    size: int = 100


class Config(BaseModel):
    """全局配置"""
    llm: Optional[LLMConfig] = None
    nuclei: Optional[NucleiConfig] = None
    fofa: Optional[FOFAConfig] = None
    log_level: str = "info"


# 默认配置
default_config = Config(
    llm=LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096
    ),
    nuclei=NucleiConfig(
        severity=["critical", "high", "medium"],
        rate_limit=150,
        threads=50
    ),
    fofa=FOFAConfig(
        size=100
    ),
    log_level="info"
)

# 当前配置
current_config = default_config.copy()


@router.get("/")
async def get_config():
    """获取配置"""
    # 隐藏敏感信息
    config = current_config.dict()
    if config.get("llm") and config["llm"].get("api_key"):
        config["llm"]["api_key"] = "***" if config["llm"]["api_key"] else None
    if config.get("fofa"):
        config["fofa"]["email"] = "***" if config["fofa"].get("email") else None
        config["fofa"]["key"] = "***" if config["fofa"].get("key") else None
    
    # 添加LLM状态
    config["llm_ready"] = is_llm_ready()
    
    return config


@router.post("/")
async def update_config(config: Config):
    """更新配置"""
    global current_config
    current_config = config
    return {"status": "updated", "config": config}


@router.post("/llm")
async def update_llm_config(config: LLMConfig):
    """更新LLM配置并初始化"""
    global current_config
    
    # 更新配置
    current_config.llm = config
    
    # 初始化LLM代理
    if config.api_key:
        init_llm_agent(
            api_key=config.api_key,
            model=config.model
        )
    
    return {"status": "updated", "llm_ready": is_llm_ready()}


@router.post("/llm/init")
async def init_llm(api_key: str, model: str = "deepseek-chat"):
    """初始化LLM代理"""
    try:
        agent = init_llm_agent(api_key=api_key, model=model)
        return {
            "status": "success",
            "llm_ready": is_llm_ready(),
            "model": model
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/llm/status")
async def get_llm_status():
    """获取LLM状态"""
    return {
        "ready": is_llm_ready(),
        "model": current_config.llm.model if current_config.llm else None
    }


@router.post("/nuclei")
async def update_nuclei_config(config: NucleiConfig):
    """更新Nuclei配置"""
    global current_config
    current_config.nuclei = config
    return {"status": "updated"}


@router.post("/fofa")
async def update_fofa_config(config: FOFAConfig):
    """更新FOFA配置"""
    global current_config
    current_config.fofa = config
    return {"status": "updated"}


@router.post("/reset")
async def reset_config():
    """重置配置"""
    global current_config
    current_config = default_config.copy()
    return {"status": "reset"}


@router.get("/providers")
async def list_llm_providers():
    """列出支持的LLM提供商"""
    return {
        "providers": [
            {"id": "deepseek", "name": "DeepSeek", "models": ["deepseek-chat", "deepseek-coder"]},
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus", "claude-3-sonnet"]},
            {"id": "google", "name": "Google Gemini", "models": ["gemini-pro"]},
            {"id": "baidu", "name": "百度文心一言", "models": ["ernie-bot"]},
            {"id": "alibaba", "name": "阿里通义千问", "models": ["qwen-turbo", "qwen-plus"]},
            {"id": "tencent", "name": "腾讯混元", "models": ["hunyuan"]},
            {"id": "zhipu", "name": "智谱GLM", "models": ["glm-4"]},
            {"id": "minimax", "name": "MiniMax", "models": ["abab6.5s-chat"]},
            {"id": "ollama", "name": "Ollama (本地)", "models": ["llama2", "mistral", "codellama"]},
            {"id": "openai-like", "name": "OpenAI兼容API", "models": ["custom"]}
        ]
    }


# 记忆系统API
@router.get("/memory/stats")
async def get_memory_stats():
    """获取记忆统计"""
    memory = get_memory_system()
    return memory.get_stats()


@router.get("/memory/search")
async def search_memory(q: str, limit: int = 10):
    """搜索记忆"""
    memory = get_memory_system()
    results = memory.search(q, limit)
    return {"results": [r.to_dict() for r in results]}


@router.get("/memory/target/{target}")
async def get_target_memories(target: str):
    """获取目标相关记忆"""
    memory = get_memory_system()
    results = memory.get_memories_by_target(target)
    return {"memories": [r.to_dict() for r in results]}


@router.post("/memory/add")
async def add_memory(content: str, memory_type: str = "fact", target: str = None, session_id: str = None, importance: float = 0.5):
    """添加记忆"""
    memory = get_memory_system()
    node_id = memory.add_memory(content, memory_type, target, session_id, importance)
    return {"status": "added", "id": node_id}
