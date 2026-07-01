"""
AI-HUB 后端服务入口

直接运行此文件即可启动服务：
    python main.py

也可使用 uvicorn 命令启动（支持热重载）：
    uvicorn app.main:app --reload --port 8001
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=False,
        log_level="info",
    )
