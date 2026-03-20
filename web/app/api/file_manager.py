"""
RedOps - 文件管理API
支持文件浏览、上传、下载等操作
"""

import os
import sys
import base64
import hashlib
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app.core.executor import get_executor

router = APIRouter(tags=["文件管理"])


# ==================== 路径模型 ====================

class PathRequest(BaseModel):
    """路径请求"""
    path: str = "."


class FileContentRequest(BaseModel):
    """文件内容请求"""
    path: str
    encoding: str = "utf-8"


class WriteFileRequest(BaseModel):
    """写入文件请求"""
    path: str
    content: str
    encoding: str = "utf-8"
    append: bool = False


class MkdirRequest(BaseModel):
    """创建目录请求"""
    path: str
    parents: bool = True


class RenameRequest(BaseModel):
    """重命名请求"""
    old_path: str
    new_path: str


class CopyRequest(BaseModel):
    """复制请求"""
    source: str
    destination: str


class DeleteRequest(BaseModel):
    """删除请求"""
    path: str
    recursive: bool = False


class ChmodRequest(BaseModel):
    """修改权限请求"""
    path: str
    mode: str  # 如 "755" 或 "u+rwx"


# ==================== 文件浏览接口 ====================

@router.post("/list")
async def list_directory(request: PathRequest):
    """列出目录内容"""
    executor = get_executor()
    result = executor.list_directory(request.path)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "访问失败"))
    
    return result


@router.get("/info")
async def get_file_info(path: str):
    """获取文件/目录详细信息"""
    executor = get_executor()
    
    try:
        abs_path = os.path.abspath(path)
        
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        stat = os.stat(abs_path)
        
        info = {
            "path": abs_path,
            "name": os.path.basename(abs_path),
            "is_file": os.path.isfile(abs_path),
            "is_dir": os.path.isdir(abs_path),
            "size": stat.st_size,
            "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "is_symlink": os.path.islink(abs_path)
        }
        
        # 计算文件哈希（对于小文件）
        if os.path.isfile(abs_path) and stat.st_size < 10 * 1024 * 1024:  # < 10MB
            try:
                with open(abs_path, 'rb') as f:
                    content = f.read()
                    info["md5"] = hashlib.md5(content).hexdigest()
                    info["sha256"] = hashlib.sha256(content).hexdigest()
            except:
                pass
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exists")
async def check_exists(request: PathRequest):
    """检查路径是否存在"""
    abs_path = os.path.abspath(request.path)
    return {
        "path": abs_path,
        "exists": os.path.exists(abs_path),
        "is_file": os.path.isfile(abs_path) if os.path.exists(abs_path) else None,
        "is_dir": os.path.isdir(abs_path) if os.path.exists(abs_path) else None
    }


# ==================== 文件读取接口 ====================

@router.post("/read")
async def read_file(request: FileContentRequest):
    """读取文件内容"""
    executor = get_executor()
    result = executor.read_file(request.path)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "读取失败"))
    
    content = result.get("content", "")
    
    # 尝试编码转换
    try:
        if request.encoding != "utf-8":
            content = content.encode("utf-8").decode(request.encoding)
    except:
        pass  # 如果转换失败，返回原始内容
    
    return {
        "path": request.path,
        "content": content,
        "size": len(content),
        "encoding": request.encoding
    }


@router.post("/read/base64")
async def read_file_base64(request: FileContentRequest):
    """以Base64格式读取文件（二进制文件）"""
    executor = get_executor()
    result = executor.read_file_binary(request.path)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "读取失败"))
    
    content = result.get("content", b"")
    
    return {
        "path": request.path,
        "content": base64.b64encode(content).decode("ascii"),
        "size": len(content),
        "encoding": "base64"
    }


@router.get("/read/lines")
async def read_file_lines(path: str, start: int = 0, count: int = 100):
    """按行读取文件（适合大文件）"""
    executor = get_executor()
    result = executor.read_file(path)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "读取失败"))
    
    lines = result.get("content", "").split("\n")
    total_lines = len(lines)
    
    return {
        "path": path,
        "total_lines": total_lines,
        "lines": lines[start:start+count],
        "start": start,
        "count": count
    }


# ==================== 文件写入接口 ====================

@router.post("/write")
async def write_file(request: WriteFileRequest):
    """写入文件"""
    executor = get_executor()
    
    try:
        abs_path = os.path.abspath(request.path)
        
        # 确保目录存在
        parent_dir = os.path.dirname(abs_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        mode = "a" if request.append else "w"
        
        with open(abs_path, mode, encoding=request.encoding) as f:
            f.write(request.content)
        
        return {
            "success": True,
            "path": abs_path,
            "size": len(request.content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/write/base64")
async def write_file_base64(path: str, content: str):
    """以Base64格式写入文件（二进制文件）"""
    executor = get_executor()
    
    try:
        abs_path = os.path.abspath(path)
        
        # 确保目录存在
        parent_dir = os.path.dirname(abs_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # 解码Base64
        data = base64.b64decode(content)
        
        with open(abs_path, "wb") as f:
            f.write(data)
        
        return {
            "success": True,
            "path": abs_path,
            "size": len(data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文件操作接口 ====================

@router.post("/mkdir")
async def make_directory(request: MkdirRequest):
    """创建目录"""
    executor = get_executor()
    
    try:
        abs_path = os.path.abspath(request.path)
        
        if request.parents:
            os.makedirs(abs_path, exist_ok=True)
        else:
            os.mkdir(abs_path)
        
        return {
            "success": True,
            "path": abs_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
async def rename_file(request: RenameRequest):
    """重命名/移动文件"""
    executor = get_executor()
    
    try:
        old_path = os.path.abspath(request.old_path)
        new_path = os.path.abspath(request.new_path)
        
        # 确保目标目录存在
        parent_dir = os.path.dirname(new_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        os.rename(old_path, new_path)
        
        return {
            "success": True,
            "old_path": old_path,
            "new_path": new_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/copy")
async def copy_file(request: CopyRequest):
    """复制文件"""
    executor = get_executor()
    
    try:
        import shutil
        source = os.path.abspath(request.source)
        dest = os.path.abspath(request.destination)
        
        # 如果目标是目录，复制到目录下
        if os.path.isdir(dest):
            dest = os.path.join(dest, os.path.basename(source))
        
        # 确保目标目录存在
        parent_dir = os.path.dirname(dest)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        if os.path.isdir(source):
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
        
        return {
            "success": True,
            "source": source,
            "destination": dest
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_file(request: DeleteRequest):
    """删除文件/目录"""
    executor = get_executor()
    
    try:
        abs_path = os.path.abspath(request.path)
        
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        if os.path.isdir(abs_path):
            if request.recursive:
                import shutil
                shutil.rmtree(abs_path)
            else:
                os.rmdir(abs_path)
        else:
            os.remove(abs_path)
        
        return {
            "success": True,
            "path": abs_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chmod")
async def change_permissions(request: ChmodRequest):
    """修改文件权限（仅Linux）"""
    executor = get_executor()
    
    if os.name == 'nt':
        raise HTTPException(status_code=400, detail="Windows不支持chmod")
    
    try:
        abs_path = os.path.abspath(request.path)
        mode = int(request.mode, 8)
        
        os.chmod(abs_path, mode)
        
        return {
            "success": True,
            "path": abs_path,
            "mode": request.mode
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文件上传下载接口 ====================

@router.post("/upload")
async def upload_file(path: str, file: UploadFile = File(...)):
    """上传文件"""
    try:
        abs_path = os.path.abspath(path)
        
        # 如果path是目录，保存到该目录下
        if os.path.isdir(abs_path):
            abs_path = os.path.join(abs_path, file.filename)
        else:
            # 确保目录存在
            parent_dir = os.path.dirname(abs_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
        
        content = await file.read()
        
        with open(abs_path, "wb") as f:
            f.write(content)
        
        return {
            "success": True,
            "path": abs_path,
            "filename": file.filename,
            "size": len(content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
async def download_file(path: str):
    """下载文件（返回Base64）"""
    executor = get_executor()
    result = executor.read_file_binary(path)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "读取失败"))
    
    content = result.get("content", b"")
    
    return {
        "path": path,
        "content": base64.b64encode(content).decode("ascii"),
        "size": len(content),
        "filename": os.path.basename(path)
    }


# ==================== 搜索接口 ====================

@router.post("/search")
async def search_files(request: PathRequest, pattern: str = ".*", recursive: bool = True):
    """搜索文件"""
    import re
    
    try:
        abs_path = os.path.abspath(request.path)
        
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        regex = re.compile(pattern)
        results = []
        
        if os.path.isfile(abs_path):
            if regex.search(os.path.basename(abs_path)):
                results.append(abs_path)
        else:
            if recursive:
                for root, dirs, files in os.walk(abs_path):
                    for name in files:
                        if regex.search(name):
                            results.append(os.path.join(root, name))
            else:
                for name in os.listdir(abs_path):
                    full_path = os.path.join(abs_path, name)
                    if os.path.isfile(full_path) and regex.search(name):
                        results.append(full_path)
        
        return {
            "path": abs_path,
            "pattern": pattern,
            "count": len(results),
            "results": results[:100]  # 限制返回数量
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drives")
async def list_drives():
    """列出所有驱动器（Windows）或挂载点（Linux）"""
    drives = []
    
    if os.name == 'nt':  # Windows
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append({
                    "path": drive,
                    "name": drive,
                    "type": "drive"
                })
    else:  # Linux
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        mount_point = parts[1]
                        if mount_point.startswith("/"):
                            drives.append({
                                "path": mount_point,
                                "name": mount_point,
                                "type": "mount"
                            })
        except:
            drives.append({"path": "/", "name": "/", "type": "root"})
    
    return {"drives": drives}
