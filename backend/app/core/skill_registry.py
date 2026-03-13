"""
RedOps Web - Skill系统
可动态加载的技能模块
"""

import os
import json
import importlib.util
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """技能基类"""
    
    name: str = "base_skill"
    description: str = "基础技能"
    category: str = "general"
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """获取技能参数 schema"""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        schema = self.get_schema()
        required = schema.get("required", [])
        
        for key in required:
            if key not in params:
                return False
        return True


class SkillRegistry:
    """技能注册表 - 管理所有技能"""
    
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, BaseSkill] = {}
        self.categories: Dict[str, List[str]] = {}
        self._load_builtin_skills()
    
    def _load_builtin_skills(self):
        """加载内置技能"""
        # 扫描技能
        self.register(PortScanSkill())
        self.register(VulnScanSkill())
        self.register(FOFASkill())
        self.register(POCVerifySkill())
        
        # 分析技能
        self.register(JSAnalysisSkill())
        self.register(TrafficCaptureSkill())
        
        # 工具技能
        self.register(SubdomainEnumSkill())
        self.register(DirScanSkill())
        self.register(CMSIdentifySkill())
        
        # 报告技能
        self.register(ReportGenSkill())
    
    def register(self, skill: BaseSkill):
        """注册技能"""
        self.skills[skill.name] = skill
        
        if skill.category not in self.categories:
            self.categories[skill.category] = []
        self.categories[skill.category].append(skill.name)
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list_skills(self, category: str = None) -> List[Dict[str, Any]]:
        """列出技能"""
        result = []
        
        if category:
            skill_names = self.categories.get(category, [])
        else:
            skill_names = list(self.skills.keys())
        
        for name in skill_names:
            skill = self.skills.get(name)
            if skill:
                result.append({
                    "name": skill.name,
                    "description": skill.description,
                    "category": skill.category,
                    "schema": skill.get_schema()
                })
        
        return result
    
    def list_categories(self) -> List[str]:
        """列出分类"""
        return list(self.categories.keys())
    
    def execute_skill(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        skill = self.get_skill(name)
        if not skill:
            return {"error": f"Skill '{name}' not found"}
        
        if not skill.validate_params(params):
            return {"error": "Invalid parameters", "schema": skill.get_schema()}
        
        try:
            return skill.execute(params)
        except Exception as e:
            return {"error": str(e)}


# ==================== 内置技能 ====================

class PortScanSkill(BaseSkill):
    """端口扫描技能"""
    name = "port_scan"
    description = "对目标进行端口扫描，检测开放端口和服务"
    category = "scan"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标IP或域名"},
            "ports": {"type": "string", "description": "端口范围，如 1-1000"},
            "speed": {"type": "string", "description": "扫描速度: fast/normal/slow", "default": "normal"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 这里调用实际的端口扫描工具
        return {
            "skill": self.name,
            "status": "completed",
            "target": params.get("target"),
            "result": {
                "open_ports": [22, 80, 443, 3306, 6379],
                "services": {
                    "22": "ssh",
                    "80": "http",
                    "443": "https",
                    "3306": "mysql",
                    "6379": "redis"
                }
            }
        }


class VulnScanSkill(BaseSkill):
    """漏洞扫描技能"""
    name = "vuln_scan"
    description = "使用Nuclei进行自动化漏洞扫描"
    category = "scan"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标URL"},
            "severity": {"type": "array", "description": "漏洞等级筛选", "default": ["critical", "high", "medium"]},
            "tags": {"type": "array", "description": "漏洞标签"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "status": "started",
            "target": params.get("target"),
            "message": "已启动Nuclei扫描，请等待结果"
        }


class FOFASkill(BaseSkill):
    """FOFA资产搜索技能"""
    name = "fofa_search"
    description = "使用FOFA搜索同类网站资产"
    category = "recon"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "query": {"type": "string", "description": "FOFA查询语句"},
            "size": {"type": "integer", "description": "返回数量", "default": 10}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "query": params.get("query"),
            "status": "ready",
            "message": "FOFA搜索已准备就绪"
        }


class POCVerifySkill(BaseSkill):
    """POC验证技能"""
    name = "poc_verify"
    description = "使用自定义POC验证漏洞"
    category = "exploit"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标URL"},
            "poc_name": {"type": "string", "description": "POC名称"},
            "poc_content": {"type": "string", "description": "POC内容(YAML)"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "target": params.get("target"),
            "status": "ready",
            "message": "POC验证已准备就绪"
        }


class JSAnalysisSkill(BaseSkill):
    """JS分析技能"""
    name = "js_analyze"
    description = "分析页面JavaScript，提取敏感信息"
    category = "analyze"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标URL"},
            "deep": {"type": "boolean", "description": "深度分析", "default": False}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "target": params.get("target"),
            "status": "ready",
            "message": "JS分析已准备就绪"
        }


class TrafficCaptureSkill(BaseSkill):
    """流量抓取技能"""
    name = "traffic_capture"
    description = "抓取和分析网络流量"
    category = "analyze"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标"},
            "interface": {"type": "string", "description": "网络接口"},
            "filter": {"type": "string", "description": "BPF过滤规则"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "status": "ready",
            "message": "流量抓取已准备就绪"
        }


class SubdomainEnumSkill(BaseSkill):
    """子域名枚举技能"""
    name = "subdomain_enum"
    description = "枚举目标子域名"
    category = "recon"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "domain": {"type": "string", "description": "目标域名"},
            "wordlist": {"type": "string", "description": "字典文件"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "status": "ready",
            "message": "子域名枚举已准备就绪"
        }


class DirScanSkill(BaseSkill):
    """目录扫描技能"""
    name = "dir_scan"
    description = "扫描网站目录和文件"
    category = "scan"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标URL"},
            "wordlist": {"type": "string", "description": "字典文件"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "status": "ready",
            "message": "目录扫描已准备就绪"
        }


class CMSIdentifySkill(BaseSkill):
    """CMS识别技能"""
    name = "cms_identify"
    description = "识别网站CMS类型"
    category = "identify"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "target": {"type": "string", "description": "目标URL"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "status": "ready",
            "message": "CMS识别已准备就绪"
        }


class ReportGenSkill(BaseSkill):
    """报告生成技能"""
    name = "report_gen"
    description = "生成渗透测试报告"
    category = "util"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "format": {"type": "string", "description": "报告格式: html/markdown/pdf", "default": "html"},
            "template": {"type": "string", "description": "报告模板"}
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "format": params.get("format", "html"),
            "status": "ready",
            "message": "报告生成已准备就绪"
        }


# 全局技能注册表
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取技能注册表"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
