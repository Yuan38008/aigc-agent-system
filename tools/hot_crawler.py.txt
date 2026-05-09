# tools/hot_crawler.py - 热榜数据抓取工具
import requests
import json
from datetime import datetime
from loguru import logger
from typing import List, Dict

class HotCrawler:
    """热榜数据爬取工具"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def get_weibo_hot(self) -> List[Dict]:
        """获取微博热搜"""
        try:
            url = "https://weibo.com/ajax/side/hotSearch"
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            
            topics = []
            for item in data.get("data", {}).get("realtime", [])[:20]:
                topics.append({
                    "title": item.get("note", ""),
                    "hot_value": item.get("num", 0),
                    "source": "微博热搜",
                    "timestamp": datetime.now().isoformat()
                })
            return topics
        except Exception as e:
            logger.error(f"微博热搜获取失败: {e}")
            return self._get_mock_hot_data("微博热搜")
    
    def get_zhihu_hot(self) -> List[Dict]:
        """获取知乎热榜"""
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
            params = {"limit": 20}
            resp = requests.get(url, headers=self.headers, 
                              params=params, timeout=10)
            data = resp.json()
            
            topics = []
            for item in data.get("data", [])[:20]:
                target = item.get("target", {})
                topics.append({
                    "title": target.get("title", ""),
                    "hot_value": item.get("detail_text", "0").replace("万热度", ""),
                    "source": "知乎热榜",
                    "timestamp": datetime.now().isoformat()
                })
            return topics
        except Exception as e:
            logger.error(f"知乎热榜获取失败: {e}")
            return self._get_mock_hot_data("知乎热榜")
    
    def get_bilibili_hot(self) -> List[Dict]:
        """获取B站热门"""
        try:
            url = "https://api.bilibili.com/x/web-interface/ranking/v2"
            params = {"rid": 0, "type": "all"}
            resp = requests.get(url, headers=self.headers, 
                              params=params, timeout=10)
            data = resp.json()
            
            topics = []
            for item in data.get("data", {}).get("list", [])[:20]:
                topics.append({
                    "title": item.get("title", ""),
                    "hot_value": item.get("stat", {}).get("view", 0),
                    "source": "B站热门",
                    "timestamp": datetime.now().isoformat()
                })
            return topics
        except Exception as e:
            logger.error(f"B站热门获取失败: {e}")
            return self._get_mock_hot_data("B站热门")
    
    def _get_mock_hot_data(self, source: str) -> List[Dict]:
        """获取失败时返回模拟数据（用于演示）"""
        mock_topics = [
            "AI工具改变工作方式", "年轻人如何规划职业发展",
            "退伍军人的转型之路", "研究生期间如何赚钱",
            "AIGC视频制作教程", "短视频运营核心技巧"
        ]
        return [
            {
                "title": topic,
                "hot_value": 10000 - i * 1000,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            for i, topic in enumerate(mock_topics)
        ]
    
    def get_all_hot_topics(self) -> List[Dict]:
        """聚合所有平台热榜"""
        all_topics = []
        all_topics.extend(self.get_weibo_hot())
        all_topics.extend(self.get_zhihu_hot())
        all_topics.extend(self.get_bilibili_hot())
        
        # 按热度排序
        all_topics.sort(
            key=lambda x: int(str(x.get("hot_value", 0)).replace(",", "")), 
            reverse=True
        )
        
        logger.info(f"共获取热榜话题 {len(all_topics)} 条")
        return all_topics
