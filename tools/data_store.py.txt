# tools/data_store.py - 数据存储工具
import json
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

class DataStore:
    """轻量级JSON数据存储"""
    
    def __init__(self, base_dir: str = "./output"):
        self.base_dir = Path(base_dir)
        self._init_dirs()
    
    def _init_dirs(self):
        """初始化目录结构"""
        dirs = ["topics", "scripts", "videos", "reports", "logs"]
        for d in dirs:
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)
    
    def save(self, category: str, data: dict, filename: str = None) -> str:
        """保存数据"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{category}_{timestamp}.json"
        
        filepath = self.base_dir / category / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存: {filepath}")
        return str(filepath)
    
    def load(self, category: str, filename: str) -> dict:
        """加载数据"""
        filepath = self.base_dir / category / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_files(self, category: str) -> list:
        """列出目录下所有文件"""
        category_dir = self.base_dir / category
        return [f.name for f in category_dir.glob("*.json")]
    
    def save_report(self, report: dict) -> str:
        """保存运行报告"""
        return self.save("reports", report)
