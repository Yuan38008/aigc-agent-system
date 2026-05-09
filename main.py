# main.py - 系统主入口
from orchestrator import MultiAgentOrchestrator
from loguru import logger
import sys

def main():
    """主函数"""
    logger.add(
        "./output/logs/system_{time}.log",
        rotation="1 day",
        level="INFO"
    )
    
    logger.info("=" * 50)
    logger.info("AIGC多Agent内容生产系统启动")
    logger.info("=" * 50)
    
    try:
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run_pipeline()
        
        if result.get("status") == "completed":
            logger.success("系统运行成功")
            sys.exit(0)
        else:
            logger.error("系统运行异常")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户手动终止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"系统异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
