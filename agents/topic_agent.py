# agents/topic_agent.py - 选题Agent
from openai import OpenAI
from config import config
from tools.hot_crawler import HotCrawler
from tools.data_store import DataStore
from loguru import logger
from typing import List, Dict
import json

class TopicAgent:
    """
    选题Agent
    职责：分析热榜数据，结合账号定位，输出最优选题方案
    """
    
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.crawler = HotCrawler()
        self.store = DataStore()
        self.agent_name = "TopicAgent"
        
    def _build_system_prompt(self) -> str:
        return f"""你是一个专业的短视频选题分析专家。
        
你的任务是：
1. 分析提供的热榜数据
2. 结合账号定位（{config.ACCOUNT_STYLE}）筛选最适合的选题
3. 对每个选题进行爆款概率评分（0-100分）
4. 输出结构化的选题方案

评分维度：
- 话题热度（30分）：当前话题的热度和讨论量
- 内容适配度（30分）：与账号定位的匹配程度  
- 制作可行性（20分）：是否能用AIGC工具快速制作
- 差异化空间（20分）：是否有独特切入角度

输出格式要求：严格按JSON格式输出，不要有其他文字。"""

    def _build_user_prompt(self, hot_topics: List[Dict]) -> str:
        topics_str = json.dumps(hot_topics[:30], ensure_ascii=False, indent=2)
        return f"""请分析以下热榜数据，为{config.TARGET_PLATFORM}平台的
{config.ACCOUNT_STYLE}账号筛选出最佳的5个选题方案。

热榜数据：
{topics_str}

请输出以下JSON格式：
{{
  "analysis_time": "分析时间",
  "platform": "目标平台",
  "selected_topics": [
    {{
      "rank": 1,
      "title": "选题标题",
      "angle": "独特切入角度",
      "score": 85,
      "score_breakdown": {{
        "heat": 25,
        "fit": 28,
        "feasibility": 18,
        "differentiation": 14
      }},
      "content_direction": "内容方向描述",
      "target_audience": "目标受众",
      "estimated_duration": "建议视频时长",
      "aigc_possibility": "AIGC制作可行性说明",
      "hook_suggestion": "开头钩子建议"
    }}
  ],
  "trend_insight": "整体趋势洞察"
}}"""

    def run(self) -> Dict:
        """执行选题分析"""
        logger.info(f"[{self.agent_name}] 开始执行选题分析...")
        
        # Step 1: 抓取热榜数据
        logger.info(f"[{self.agent_name}] 正在抓取热榜数据...")
        hot_topics = self.crawler.get_all_hot_topics()
        
        # Step 2: 调用LLM分析
        logger.info(f"[{self.agent_name}] 正在进行AI分析...")
        
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(hot_topics)}
        ]
        
        result = None
        for attempt in range(config.MAX_RETRY):
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=3000
                )
                
                content = response.choices[0].message.content
                # 清理可能的markdown代码块
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                result = json.loads(content)
                break
                
            except json.JSONDecodeError as e:
                logger.warning(f"[{self.agent_name}] JSON解析失败，重试 {attempt+1}/{config.MAX_RETRY}")
                if attempt == config.MAX_RETRY - 1:
                    result = self._fallback_result(hot_topics)
            except Exception as e:
                logger.error(f"[{self.agent_name}] API调用失败: {e}")
                if attempt == config.MAX_RETRY - 1:
                    result = self._fallback_result(hot_topics)
        
        # Step 3: 保存结果
        if result:
            self.store.save("topics", result)
            logger.success(f"[{self.agent_name}] 选题分析完成，共 {len(result.get('selected_topics', []))} 个选题")
        
        return result
    
    def _fallback_result(self, hot_topics: List[Dict]) -> Dict:
        """降级处理：当AI分析失败时返回基础结果"""
        return {
            "analysis_time": "fallback",
            "platform": config.TARGET_PLATFORM,
            "selected_topics": [
                {
                    "rank": i+1,
                    "title": topic["title"],
                    "angle": "待AI分析",
                    "score": 60,
                    "content_direction": "待确定",
                    "target_audience": "通用受众",
                    "estimated_duration": "60-90秒",
                    "aigc_possibility": "高",
                    "hook_suggestion": "待生成"
                }
                for i, topic in enumerate(hot_topics[:5])
            ],
            "trend_insight": "AI分析暂时不可用，已返回热度最高话题"
        }
