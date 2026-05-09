# agents/production_agent.py - 制作Agent
from openai import OpenAI
from config import config
from tools.data_store import DataStore
from loguru import logger
from typing import Dict, List
import json
import requests

class ProductionAgent:
    """
    制作Agent
    职责：根据脚本生成AIGC提示词，调用视频生成API，输出素材包
    """
    
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.store = DataStore()
        self.agent_name = "ProductionAgent"
    
    def _optimize_prompts(self, script: Dict) -> List[Dict]:
        """
        使用LLM优化每个镜头的AIGC提示词
        将中文场景描述转化为最优的英文提示词
        """
        shots = script.get("shots", [])
        optimized_shots = []
        
        for shot in shots:
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": """你是AIGC视频生成提示词专家。
将场景描述转化为适合即梦/可灵/Vidu等工具的高质量提示词。
提示词要求：
- 英文为主（效果更好）
- 包含：主体、动作、环境、光线、风格、镜头
- 避免：抽象概念、版权内容、不可生成的元素
- 格式：直接输出提示词，不要解释"""
                        },
                        {
                            "role": "user",
                            "content": f"""
场景描述：{shot.get('scene_prompt')}
镜头运动：{shot.get('camera')}
情绪目标：{shot.get('emotion_target')}
时长：{shot.get('duration')}

请输出优化后的AIGC视频生成提示词（正向提示词+负向提示词）：
格式：
正向：[提示词]
负向：[负向提示词]"""
                        }
                    ],
                    temperature=0.6,
                    max_tokens=500
                )
                
                prompt_text = response.choices[0].message.content
                lines = prompt_text.strip().split("\n")
                
                positive_prompt = ""
                negative_prompt = ""
                
                for line in lines:
                    if line.startswith("正向：") or line.startswith("正向:"):
                        positive_prompt = line.replace("正向：", "").replace("正向:", "").strip()
                    elif line.startswith("负向：") or line.startswith("负向:"):
                        negative_prompt = line.replace("负向：", "").replace("负向:", "").strip()
                
                optimized_shot = shot.copy()
                optimized_shot["aigc_positive_prompt"] = positive_prompt or shot.get("scene_prompt", "")
                optimized_shot["aigc_negative_prompt"] = negative_prompt or "blurry, low quality, distorted"
                optimized_shots.append(optimized_shot)
                
            except Exception as e:
                logger.error(f"[{self.agent_name}] 提示词优化失败: {e}")
                shot["aigc_positive_prompt"] = shot.get("scene_prompt", "")
                shot["aigc_negative_prompt"] = "blurry, low quality, distorted"
                optimized_shots.append(shot)
        
        return optimized_shots
    
    def _call_aigc_api(self, prompt: str, duration: str) -> Dict:
        """
        调用AIGC视频生成API
        当前为模拟调用，配置API Key后自动切换为真实调用
        """
        if config.KLING_API_KEY:
            return self._call_kling_api(prompt, duration)
        elif config.JIMENG_API_KEY:
            return self._call_jimeng_api(prompt, duration)
        else:
            # 模拟模式：返回占位结果
            logger.warning(f"[{self.agent_name}] 未配置AIGC API Key，使用模拟模式")
            return {
                "status": "simulated",
                "prompt": prompt,
                "duration": duration,
                "video_url": f"[待生成：{prompt[:50]}...]",
                "note": "请配置KLING_API_KEY或JIMENG_API_KEY以启用真实生成"
            }
    
    def
