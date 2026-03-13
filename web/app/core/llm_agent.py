"""
RedOps Web - LLM智能助手模块
支持DeepSeek等大语言模型，实现自主推理和实验
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class LLMAgent:
    """LLM智能代理 - 具有自主推理和实验能力"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.conversations: Dict[str, List[Dict]] = {}  # session_id -> messages
        self.max_iterations = 10  # 最大迭代次数
        self.thinking_depth = 3  # 思考深度
    
    def create_session(self, session_id: str, system_prompt: str = None) -> bool:
        """创建新会话"""
        if system_prompt is None:
            system_prompt = """你是一个专业的渗透测试助手，具有以下能力：
1. 自主思考和分析目标系统
2. 根据测试结果进行迭代实验
3. 能够调用各种工具进行测试
4. 清晰记录测试过程和结果

在渗透测试过程中，你需要：
- 分析目标信息
- 制定测试计划
- 执行测试并记录结果
- 根据结果调整策略
- 总结发现的安全问题

请用中文回复，保持专业性和准确性。"""
        
        self.conversations[session_id] = [
            {"role": "system", "content": system_prompt}
        ]
        return True
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        if session_id not in self.conversations:
            self.create_session(session_id)
        
        self.conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """获取会话历史"""
        return self.conversations.get(session_id, [])
    
    def chat(self, session_id: str, message: str, temperature: float = 0.7) -> Dict[str, Any]:
        """发送聊天请求"""
        if session_id not in self.conversations:
            self.create_session(session_id)
        
        # 添加用户消息
        self.add_message(session_id, "user", message)
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": self.conversations[session_id],
                    "temperature": temperature,
                    "max_tokens": 4096
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                
                # 添加助手回复
                self.add_message(session_id, "assistant", assistant_message)
                
                return {
                    "success": True,
                    "message": assistant_message,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API错误: {response.status_code}",
                    "detail": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def autonomous_thinking(self, session_id: str, context: Dict[str, Any], max_iterations: int = None) -> Dict[str, Any]:
        """
        自主思考和实验循环
        模仿OpenClaw的智能推理能力
        """
        if max_iterations is None:
            max_iterations = self.max_iterations
        
        results = {
            "iterations": [],
            "final_plan": None,
            "actions_taken": [],
            "findings": []
        }
        
        # 构建上下文
        context_prompt = f"""
当前测试上下文：
- 目标: {context.get('target', '未指定')}
- 已发现信息: {context.get('discovered', [])}
- 已执行测试: {context.get('executed', [])}
- 当前状态: {context.get('status', '初始化')}

请进行深度思考，分析当前状况，然后决定下一步行动。
"""
        
        for i in range(max_iterations):
            iteration = {
                "step": i + 1,
                "timestamp": datetime.now().isoformat(),
                "thinking": None,
                "action": None,
                "result": None,
                "analysis": None
            }
            
            # 发送思考请求
            response = self.chat(session_id, context_prompt + f"\n\n这是第 {i+1} 次迭代思考。请分析当前状况并决定下一步行动。")
            
            if not response.get("success"):
                iteration["error"] = response.get("error")
                results["iterations"].append(iteration)
                break
            
            thinking = response["message"]
            iteration["thinking"] = thinking
            
            # 分析思考结果，提取行动
            action = self._parse_action(thinking)
            iteration["action"] = action
            
            if action:
                results["actions_taken"].append(action)
                
                # 执行动作（这里只是模拟，实际会调用相应模块）
                result = self._execute_action(action, context)
                iteration["result"] = result
                
                if result.get("finding"):
                    results["findings"].append(result["finding"])
                
                # 更新上下文
                context_prompt += f"\n\n第 {i+1} 步行动结果: {result.get('summary', '执行完成')}"
                
                # 检查是否完成
                if result.get("complete"):
                    results["final_plan"] = thinking
                    break
            else:
                # 没有具体行动，可能是总结
                iteration["analysis"] = thinking
                if "总结" in thinking or "完成" in thinking:
                    results["final_plan"] = thinking
                    break
            
            results["iterations"].append(iteration)
        
        return results
    
    def _parse_action(self, thinking: str) -> Optional[Dict[str, Any]]:
        """从思考中解析出具体行动"""
        thinking_lower = thinking.lower()
        
        # 检测关键词
        if "扫描" in thinking or "scan" in thinking_lower:
            return {"type": "scan", "tool": "nuclei"}
        elif "poc" in thinking_lower or "验证" in thinking:
            return {"type": "poc", "tool": "custom"}
        elif "fofa" in thinking_lower or "搜索" in thinking:
            return {"type": "recon", "tool": "fofa"}
        elif "端口" in thinking or "port" in thinking_lower:
            return {"type": "port_scan", "tool": "nmap"}
        elif "js" in thinking_lower or "逆向" in thinking:
            return {"type": "js_reverse", "tool": "manual"}
        elif "越权" in thinking or "idor" in thinking_lower:
            return {"type": "idor", "tool": "manual"}
        elif "抓包" in thinking or "流量" in thinking:
            return {"type": "traffic", "tool": "burp"}
        
        return None
    
    def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行动作"""
        action_type = action.get("type")
        
        return {
            "action": action_type,
            "tool": action.get("tool"),
            "summary": f"准备执行 {action_type} 测试",
            "complete": False,
            "finding": None
        }
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_session_count(self) -> int:
        """获取会话数量"""
        return len(self.conversations)


# 全局LLM代理实例
_llm_agent: Optional[LLMAgent] = None


def get_llm_agent() -> Optional[LLMAgent]:
    """获取LLM代理实例"""
    return _llm_agent


def init_llm_agent(api_key: str, model: str = "deepseek-chat") -> LLMAgent:
    """初始化LLM代理"""
    global _llm_agent
    _llm_agent = LLMAgent(api_key=api_key, model=model)
    return _llm_agent


def is_llm_ready() -> bool:
    """检查LLM是否已初始化"""
    return _llm_agent is not None
