"""
RedOps Web - FOFA集成模块
"""

import requests
import base64
from typing import List, Dict, Any, Optional


class FOFAClient:
    """FOFA客户端"""
    
    def __init__(self, email: str = None, key: str = None):
        self.email = email or ""
        self.key = key or ""
        self.base_url = "https://fofa.info/api/v1"
    
    def search(self, query: str, size: int = 100, page: int = 1) -> Dict[str, Any]:
        """
        搜索FOFA
        
        Args:
            query: FOFA查询语句
            size: 返回数量
            page: 页码
        
        Returns:
            搜索结果
        """
        # 编码查询语句
        qbase64 = base64.b64encode(query.encode()).decode()
        
        # 构建请求URL
        url = f"{self.base_url}/search/all"
        params = {
            "qbase64": qbase64,
            "size": size,
            "page": page,
            "fields": "host,title,ip,port,server,domain,os,country,city,banner"
        }
        
        if self.email and self.key:
            params["email"] = self.email
            params["key"] = self.key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get("error"):
                return {"error": data["error"]}
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "host": item.get("host", ""),
                    "title": item.get("title", ""),
                    "ip": item.get("ip", ""),
                    "port": item.get("port", ""),
                    "server": item.get("server", ""),
                    "domain": item.get("domain", ""),
                    "os": item.get("os", ""),
                    "country": item.get("country", ""),
                    "city": item.get("city", "")
                })
            
            return {
                "size": len(results),
                "results": results,
                "query": query
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_host(self, domain: str, size: int = 100) -> Dict[str, Any]:
        """搜索指定域名的所有资产"""
        query = f'domain="{domain}"'
        return self.search(query, size)
    
    def search_ip(self, ip: str, size: int = 100) -> Dict[str, Any]:
        """搜索指定IP的所有资产"""
        query = f'ip="{ip}"'
        return self.search(query, size)
    
    def search_by_keyword(self, keyword: str, size: int = 100) -> Dict[str, Any]:
        """根据关键词搜索"""
        query = f'title="{keyword}" || banner="{keyword}" || server="{keyword}"'
        return self.search(query, size)
    
    def search_by_protocol(self, protocol: str, size: int = 100) -> Dict[str, Any]:
        """根据协议搜索"""
        query = f'protocol="{protocol}"'
        return self.search(query, size)


# 常用FOFA查询语法
FOFA_QUERIES = {
    "登录页面": 'title="登录" || title="login" || title="管理后台"',
    "后台": 'title="管理" || title="admin" || title="console"',
    "摄像头": 'protocol="rtsp" || product="Hikvision" || product="Dahua"',
    "数据库": 'protocol="mysql" || protocol="postgresql" || protocol="mongodb"',
    "Redis": 'protocol="redis"',
    "Elasticsearch": 'protocol="elasticsearch"',
    "Jenkins": 'product="Jenkins"',
    "Spring": 'framework="spring" || title="Spring"',
    "Shiro": 'app="Apache Shiro"',
    "通达OA": 'product="通达OA"',
    "泛微OA": 'product="泛微OA" || product="weaver"',
    "致远OA": 'product="致远OA"',
    "漏洞未修复": 'vuln="CVE-2023" && status!="patched"'
}


def build_query(keyword: str, **kwargs) -> str:
    """
    构建FOFA查询语句
    
    Args:
        keyword: 关键词
        **kwargs: 其他过滤条件
    
    Returns:
        FOFA查询语句
    """
    query_parts = []
    
    # 关键词
    if keyword:
        query_parts.append(f'(title="{keyword}" || title="{keyword}" || banner="{keyword}")')
    
    # 端口
    if kwargs.get("port"):
        query_parts.append(f'port="{kwargs["port"]}"')
    
    # 协议
    if kwargs.get("protocol"):
        query_parts.append(f'protocol="{kwargs["protocol"]}"')
    
    # 国家
    if kwargs.get("country"):
        query_parts.append(f'country="{kwargs["country"]}"')
    
    # 厂商
    if kwargs.get("vendor"):
        query_parts.append(f'vendor="{kwargs["vendor"]}"')
    
    # 产品
    if kwargs.get("product"):
        query_parts.append(f'product="{kwargs["product"]}"')
    
    return " && ".join(query_parts)
