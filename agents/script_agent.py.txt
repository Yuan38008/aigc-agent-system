# agents/script_agent.py - 脚本Agent
from openai import OpenAI
from config import config
from tools.data_store import DataStore
from loguru import logger
from typing import Dict, List
import json

class ScriptAgent:
    """
    脚本Agent
    职责：基于选题进行长链推理，生成完整分镜脚本
    使用Chain-of-Thought确保脚本质量
    """
    
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.store = DataStore()
        self.agent_name = "ScriptAgent"
    
    def _build_cot_prompt(self, topic: Dict) -> List[Dict]:
        """构建Chain-of-Thought多轮对话"""
        
        system_prompt = """你是一个专业的短视频脚本创作专家，擅长为AIGC视频生成提供精准的分镜脚本。

你的创作遵循以下原则：
1. 黄金3秒法则：开头必须有强钩子
2. 情绪曲线：起伏有致，保持观看欲
3. AIGC友好：每个镜头描述要适合AI视频生成
4. 平台调性：符合目标平台的内容风格"""

        messages = [
            {"role": "system", "content": system_prompt},
            
            # 第一轮：分析选题
            {"role": "user", "content": f"""
我需要为以下选题创作短视频脚本，请先分析这个选题的核心价值和受众心理：

选题：{topic.get('title')}
切入角度：{topic.get('angle')}
目标受众：{topic.get('target_audience')}
视频时长：{topic.get('estimated_duration')}
钩子建议：{topic.get('hook_suggestion')}

请分析：1.受众核心痛点 2.内容价值主张 3.情绪触发点"""},
            
            {"role": "assistant", "content": f"""
分析{topic.get('title')}这个选题：

1. 受众核心痛点：目标受众面临信息过载和决策困难的问题，需要简洁有效的解决方案

2. 内容价值主张：提供可立即执行的实用方法，让观众感受到"学到了"的满足感

3. 情绪触发点：
   - 共鸣感："这说的就是我！"
   - 获得感："原来还可以这样！"  
   - 紧迫感："我要马上试试！"

基于以上分析，我将围绕这三个情绪节点设计脚本结构。"""},
            
            # 第二轮：生成脚本
            {"role": "user", "content": """
很好！现在请基于以上分析，生成完整的分镜脚本。

要求：
- 每个镜头包含：镜头编号、画面描述（AIGC生成用）、口播文案、时长、转场方式
- 画面描述要详细，适合直接输入AI视频生成工具
- 整体时长控制在60-90秒
- 必须有强力开头钩子和行动号召结尾

请严格按以下JSON格式输出：
{
  "topic": "选题标题",
  "total_duration": "总时长",
  "hook_type": "钩子类型",
  "shots": [
    {
      "shot_id": 1,
      "duration": "3秒",
      "scene_prompt": "适合AIGC生成的画面描述（英文效果更好）",
      "voiceover": "口播文案",
      "camera": "镜头运动方式",
      "transition": "转场方式",
      "emotion_target": "本镜头情绪目标"
    }
  ],
  "caption_suggestion": "字幕建议",
  "bgm_style": "背景音乐风格",
  "publish_time": "建议发布时间"
}"""}
        ]
        
        return messages
    
    def run(self, topic_result: Dict) -> Dict:
        """为每个选题生成脚本"""
        logger.info(f"[{self.agent_name}] 开始生成脚本...")
        
        topics = topic_result.get("selected_topics", [])
        all_scripts = []
        
        # 默认为排名第一的选题生成脚本
        # 可扩展为批量生成
        primary_topic = topics[0] if topics else {}
        
        messages = self._build_cot_prompt(primary_topic)
        
        for attempt in range(config.MAX_RETRY):
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                script = json.loads(content)
                all_scripts.append(script)
                break
                
            except Exception as e:
                logger.error(f"[{self.agent_name}] 脚本生成失败: {e}")
                if attempt == config.MAX_RETRY - 1:
                    all_scripts.append(self._fallback_script(primary_topic))
        
        result = {
            "generated_scripts": all_scripts,
            "topic_source": primary_topic.get("title", ""),
            "agent": self.agent_name
        }
        
        self.store.save("scripts", result)
        logger.success(f"[{self.agent_name}] 脚本生成完成")
        
        return result
    
    def _fallback_script(self, topic: Dict) -> Dict:
        """降级脚本模板"""
        return {
            "topic": topic.get("title", "待定"),
            "total_duration": "60秒",
            "hook_type": "问题式钩子",
            "shots": [
                {
                    "shot_id": 1,
                    "duration": "3秒",
                    "scene_prompt": "A person looking surprised at camera, modern background, cinematic",
                    "voiceover": "你知道吗？90%的人都不知道这个方法！",
                    "camera": "推镜头",
                    "transition": "硬切",
                    "emotion_target": "制造好奇"
                },
                {
                    "shot_id": 2,
                    "duration": "57秒",
                    "scene_prompt": "Tutorial style video, clean background, step by step demonstration",
                    "voiceover": "今天分享一个超实用的技巧...",
                    "camera": "固定镜头",
                    "transition": "淡出",
                    "emotion_target": "提供价值"
                }
            ],
            "caption_suggestion": "大字幕，关键词高亮",
            "bgm_style": "轻快节奏",
            "publish_time": "18:00-20:00"
        }
