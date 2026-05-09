# orchestrator.py - 多Agent调度器（核心）
from agents.topic_agent import TopicAgent
from agents.script_agent import ScriptAgent
from agents.production_agent import ProductionAgent
from agents.publish_agent import PublishAgent
from tools.data_store import DataStore
from loguru import logger
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

console = Console()

class MultiAgentOrchestrator:
    """
    多Agent协同调度器
    
    工作流：
    TopicAgent → ScriptAgent → ProductionAgent → PublishAgent
         ↑__________________________________|
                    数据闭环反馈
    """
    
    def __init__(self):
        self.topic_agent = TopicAgent()
        self.script_agent = ScriptAgent()
        self.production_agent = ProductionAgent()
        self.publish_agent = PublishAgent()
        self.store = DataStore()
        
    def run_pipeline(self) -> dict:
        """执行完整的多Agent流水线"""
        
        start_time = datetime.now()
        console.print(Panel.fit(
            "🤖 AIGC多Agent内容生产系统启动",
            style="bold blue"
        ))
        
        pipeline_result = {
            "run_id": start_time.strftime("%Y%m%d_%H%M%S"),
            "start_time": start_time.isoformat(),
            "stages": {}
        }
        
        # ========== Stage 1: 选题Agent ==========
        console.print("\n[bold cyan]▶ Stage 1/4 选题Agent运行中...[/bold cyan]")
        try:
            topic_result = self.topic_agent.run()
            pipeline_result["stages"]["topic"] = {
                "status": "success",
                "topics_count": len(topic_result.get("selected_topics", [])),
                "top_topic": topic_result.get("selected_topics", [{}])[0].get("title", "")
            }
            console.print("[green]✅ 选题分析完成[/green]")
            
            # 展示选题结果
            for i, topic in enumerate(topic_result.get("selected_topics", [])[:3]):
                console.print(
                    f"  [{i+1}] {topic.get('title')} "
                    f"(爆款评分: {topic.get('score', 0)}分)"
                )
        except Exception as e:
            logger.error(f"选题Agent失败: {e}")
            pipeline_result["stages"]["topic"] = {"status": "failed", "error": str(e)}
            return pipeline_result
        
        # ========== Stage 2: 脚本Agent ==========
        console.print("\n[bold cyan]▶ Stage 2/4 脚本Agent运行中...[/bold cyan]")
        try:
            script_result = self.script_agent.run(topic_result)
            scripts = script_result.get("generated_scripts", [])
            shots_count = len(scripts[0].get("shots", [])) if scripts else 0
            
            pipeline_result["stages"]["script"] = {
                "status": "success",
                "scripts_count": len(scripts),
                "shots_count": shots_count
            }
            console.print(f"[green]✅ 脚本生成完成，共{shots_count}个镜头[/green]")
        except Exception as e:
            logger.error(f"脚本Agent失败: {e}")
            pipeline_result["stages"]["script"] = {"status": "failed", "error": str(e)}
            return pipeline_result
        
        # ========== Stage 3: 制作Agent ==========
        console.print("\n[bold cyan]▶ Stage 3/4 制作Agent运行中...[/bold cyan]")
        try:
            production_result = self.production_agent.run(script_result)
            pipeline_result["stages"]["production"] = {
                "status": "success",
                "prompts_optimized": production_result.get("optimized_shots_count", 0)
            }
            console.print("[green]✅ AIGC制作方案生成完成[/green]")
        except Exception as e:
            logger.error(f"制作Agent失败: {e}")
            pipeline_result["stages"]["production"] = {
                "status": "failed", "error": str(e)
            }
            production_result = {}
        
        # ========== Stage 4: 发布Agent ==========
        console.print("\n[bold cyan]▶ Stage 4/4 发布Agent运行中...[/bold cyan]")
        try:
            publish_result = self.publish_agent.run(script_result, production_result)
            plan = publish_result.get("publish_plan", {})
            titles = plan.get("titles", [])
            
            pipeline_result["stages"]["publish"] = {
                "status": "success",
                "titles_generated": len(titles),
                "recommended_title": titles[0] if titles else ""
            }
            console.print("[green]✅ 发布方案生成完成[/green]")
        except Exception as e:
            logger.error(f"发布Agent失败: {e}")
            pipeline_result["stages"]["publish"] = {
                "status": "failed", "error": str(e)
            }
            publish_result = {}
        
        # ========== 汇总报告 ==========
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        
        pipeline_result["end_time"] = end_time.isoformat()
        pipeline_result["duration_seconds"] = duration
        pipeline_result["status"] = "completed"
        
        # 保存完整报告
        self.store.save_report(pipeline_result)
        
        # 打印最终报告
        console.print(Panel(
            f"""
[bold green]🎉 流水线执行完成！[/bold green]

⏱️  耗时：{duration}秒
📊 选题数：{pipeline_result['stages'].get('topic', {}).get('topics_count', 0)}个
🎬 脚本镜头：{pipeline_result['stages'].get('script', {}).get('shots_count', 0)}个
📝 推荐标题：{pipeline_result['stages'].get('publish', {}).get('recommended_title', '生成中')}

📁 结果已保存至 ./output 目录
            """,
            title="运行报告",
            style="bold green"
        ))
        
        return pipeline_result
