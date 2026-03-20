#!/usr/bin/env python
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting RedOps server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
