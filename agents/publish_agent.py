# agents/publish_agent.py - 发布Agent
from openai import OpenAI
from config import config
from tools.data_store import DataStore
from loguru import logger
from typing import Dict
import json
from datetime import datetime

class PublishAgent:
    """
    发布Agent
    职责：生成发布文案、标签、封面建议，输出完整发布包
    并将数据回传给选题Agent形成闭环
    """
    
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.store = DataStore()
        self.agent_name = "PublishAgent"
    
    def run(self, script_result: Dict, production_result: Dict) -> Dict:
        logger.info(f"[{self.agent_name}] 开始生成发布方案...")
        
        script = script_result.get("generated_scripts", [{}])[0]
        topic = script_result.get("topic_source", "")
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是短视频发布运营专家，擅长撰写高点击率的标题和标签。"
                    },
                    {
                        "role": "user",
                        "content": f"""
为以下视频生成完整发布方案：

选题：{topic}
平台：{config.TARGET_PLATFORM}
账号风格：{config.ACCOUNT_STYLE}

请输出JSON格式：
{{
  "titles": ["标题1（带emoji）", "标题2", "标题3"],
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "cover_suggestion": "封面设计建议",
  "publish_time": "最佳发布时间",
  "first_comment": "发布后第一条评论内容（引导互动）",
  "ab_test_suggestion": "A/B测试建议",
  "data_metrics": ["需要关注的数据指标"]
}}"""
                    }
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            publish_plan = json.loads(content)
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 发布方案生成失败: {e}")
            publish_plan = {
                "titles": [f"【实测有效】{topic}，建议收藏！"],
                "tags": ["干货分享", "实用技巧", "涨知识", "生活技巧", "推荐"],
                "cover_suggestion": "大字报式封面，突出核心关键词",
                "publish_time": "工作日18:00-20:00，周末10:00-12:00",
                "first_comment": "你们最想了解哪个部分？评论告诉我～",
                "ab_test_suggestion": "测试情绪型标题vs数字型标题",
                "data_metrics": ["完播率", "点赞率", "评论数", "转发数"]
            }
        
        result = {
            "publish_plan": publish_plan,
            "topic": topic,
            "generated_at": datetime.now().isoformat(),
            "agent": self.agent_name,
            "feedback_to_topic_agent": {
                "topic": topic,
                "predicted_performance": "待发布后回收数据",
                "optimization_suggestion": "根据前3小时数据决定是否加热"
            }
        }
        
        self.store.save("reports", result)
        logger.success(f"[{self.agent_name}] 发布方案生成完成")
        return result
