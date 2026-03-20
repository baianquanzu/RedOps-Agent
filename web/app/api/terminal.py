"""
RedOps - 交互式终端API
支持WebSocket实时交互的shell终端（跨平台支持）
"""

import asyncio
import subprocess
import os
import sys
import uuid
import base64
import threading
import time
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter(tags=["终端"])


# 终端会话管理
class TerminalSession:
    """终端会话"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process: Optional[subprocess.Popen] = None
        self.ws: Optional[WebSocket] = None
        self.lock = threading.Lock()
        self.is_windows = os.name == 'nt'
    
    def start_shell(self) -> bool:
        """启动shell进程"""
        try:
            if self.is_windows:  # Windows
                self.process = subprocess.Popen(
                    ["cmd.exe"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    env={**os.environ, "TERM": "xterm-256color"}
                )
            else:  # Linux - 以root用户启动，直接到root目录
                self.process = subprocess.Popen(
                    ["sudo", "su", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    cwd="/root",
                    env={**os.environ, "TERM": "xterm-256color"}
                )
            return True
        except Exception as e:
            print(f"启动shell失败: {e}")
            return False
    
    def write(self, data: bytes) -> bool:
        """写入数据到shell"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data)
                self.process.stdin.flush()
                return True
            except:
                return False
        return False
    
    def read_output(self, chunk_size: int = 1024) -> Optional[bytes]:
        """读取输出（非阻塞）"""
        if not self.process or not self.process.stdout:
            return None
        
        try:
            if self.is_windows:
                # Windows: 使用poll检测
                if self.process.poll() is not None:
                    return None
                import select
                if select.select([self.process.stdout], [], [], 0)[0]:
                    return os.read(self.process.stdout.fileno(), chunk_size)
            else:
                # Unix/Linux: 使用select
                import select
                if select.select([self.process.stdout], [], [], 0)[0]:
                    return os.read(self.process.stdout.fileno(), chunk_size)
        except:
            pass
        return None
    
    def is_alive(self) -> bool:
        """检查进程是否存活"""
        return self.process is not None and self.process.poll() is None
    
    def close(self):
        """关闭shell"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None


# 全局会话存储
sessions: Dict[str, TerminalSession] = {}
sessions_lock = threading.Lock()


def get_session(session_id: str) -> Optional[TerminalSession]:
    """获取会话"""
    with sessions_lock:
        return sessions.get(session_id)


def create_session() -> str:
    """创建新会话"""
    session_id = str(uuid.uuid4())[:8]
    with sessions_lock:
        sessions[session_id] = TerminalSession(session_id)
    return session_id


def close_session(session_id: str):
    """关闭会话"""
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id].close()
            del sessions[session_id]


# ==================== WebSocket终端接口 ====================

@router.websocket("/terminal/ws")
async def terminal_websocket(websocket: WebSocket):
    """
    WebSocket终端连接
    前端连接后会自动创建shell并开始转发数据
    """
    await websocket.accept()
    
    session_id = create_session()
    session = get_session(session_id)
    session.ws = websocket
    
    try:
        # 启动shell
        if not session.start_shell():
            await websocket.send_text("[ERROR] 无法启动终端")
            await websocket.close()
            close_session(session_id)
            return
        
        await websocket.send_text(f"[INFO] 会话 {session_id} 已创建\r\n")
        
        # 输出读取任务
        async def read_loop():
            while session.is_alive():
                try:
                    data = session.read_output()
                    if data:
                        await websocket.send_bytes(data)
                    await asyncio.sleep(0.01)
                except:
                    break
        
        # 启动读取任务
        read_task = asyncio.create_task(read_loop())
        
        # 接收前端数据
        try:
            while True:
                data = await websocket.receive_bytes()
                session.write(data)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"接收数据错误: {e}")
        finally:
            read_task.cancel()
            close_session(session_id)
            
    except Exception as e:
        print(f"终端错误: {e}")
        close_session(session_id)


@router.websocket("/terminal/{session_id}")
async def terminal_by_id(websocket: WebSocket, session_id: str):
    """通过会话ID连接终端"""
    await websocket.accept()
    
    session = get_session(session_id)
    if not session:
        # 创建新会话
        with sessions_lock:
            sessions[session_id] = TerminalSession(session_id)
        session = get_session(session_id)
        session.start_shell()
    
    session.ws = websocket
    
    try:
        # 接收前端数据
        while True:
            data = await websocket.receive_bytes()
            session.write(data)
    except WebSocketDisconnect:
        pass
    except:
        pass
    finally:
        close_session(session_id)


# ==================== REST终端接口 ====================

class CommandExecRequest(BaseModel):
    """命令执行请求"""
    command: str
    cwd: Optional[str] = None
    timeout: int = 30


@router.post("/exec")
async def exec_command(request: CommandExecRequest):
    """
    执行单条命令（REST方式）
    返回原始输出
    """
    from web.app.core.executor import get_executor
    executor = get_executor()
    
    try:
        if request.cwd:
            result = executor.execute_with_workdir(request.command, request.cwd)
        else:
            result = executor.execute(request.command, timeout=request.timeout)
        
        return {
            "success": result.get("success", False),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "returncode": result.get("returncode", -1)
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


@router.get("/sessions")
async def list_sessions():
    """列出所有终端会话"""
    with sessions_lock:
        return {
            "sessions": [
                {
                    "id": sid,
                    "alive": sess.is_alive()
                }
                for sid, sess in sessions.items()
            ]
        }


@router.delete("/session/{session_id}")
async def kill_session(session_id: str):
    """关闭指定会话"""
    close_session(session_id)
    return {"status": "ok"}


@router.delete("/sessions")
async def kill_all_sessions():
    """关闭所有会话"""
    with sessions_lock:
        for session in sessions.values():
            session.close()
        sessions.clear()
    return {"status": "ok"}
