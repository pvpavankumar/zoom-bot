
import asyncio
import signal
import sys
import os
from typing import Optional

from .core.bot_manager import BotManager
from .core.config import settings
from .utils.logging import setup_logging, get_logger
from .api.main import create_app

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

logger = get_logger(__name__)


class ZoomInterviewBotApp:

    def __init__(self):
        print("0000000000000")
        self.bot_manager: Optional[BotManager] = None
        print("completed p1")
        self.web_app = None
        self._shutdown_event = asyncio.Event()
        print("1111111111111")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        print("completed p2")

    async def start(self):
        print("2222222222222")
        logger.info("Starting Zoom Interview Bot...")
        print("completed p3")

        try:
            print("3333333333333")
            if settings.run_startup_tests:
                logger.info("🧪 Running startup validation tests...")
                print("completed p4")
                test_success = await self._run_startup_tests()
                print("4444444444444")

                if not test_success:
                    if settings.skip_tests_on_failure:
                        logger.warning("⚠️ Some startup tests failed, but continuing with bot startup...")
                        logger.warning("🔧 Please review test results and fix any issues for optimal performance")
                        print("completed p5")
                    else:
                        logger.error("❌ Startup tests failed and skip_tests_on_failure is disabled")
                        raise RuntimeError("Startup tests failed - aborting bot startup")
                else:
                    logger.info("✅ All startup tests passed! Bot is ready for operation")
                    print("5555555555555")
            else:
                logger.info("⏭️ Startup tests disabled via configuration")
                print("completed p6")


            print("6666666666666")
            self.bot_manager = BotManager()
            await self.bot_manager.start()
            print("completed p7")


            self.web_app = create_app()
            print("7777777777777")


            import uvicorn
            print("completed p8")


            logger.info(f"Starting web server on port {settings.port}")
            server_config = uvicorn.Config(
                app=self.web_app,
                host=settings.host,
                port=settings.port,
                log_level="info"
            )
            server = uvicorn.Server(server_config)


            import threading
            server_thread = threading.Thread(
                target=lambda: asyncio.run(server.serve()),
                daemon=True
            )
            server_thread.start()

            logger.info(f"Web server started at http://{settings.host}:{settings.port}")

            logger.info("Zoom Interview Bot started successfully")


            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise
        finally:
            await self.stop()

    async def _run_startup_tests(self):

        try:

            from startup_validator import run_startup_tests


            return await run_startup_tests()

        except ImportError as e:
            logger.warning(f"Could not import startup validator: {e}")
            logger.warning("Startup validation not available - continuing with bot startup")
            return True
        except Exception as e:
            logger.error(f"Error running startup validation: {e}")
            logger.warning("Validation execution failed - treating as validation failure")
            return False

    async def stop(self):

        logger.info("Stopping Zoom Interview Bot...")

        if self.bot_manager:
            await self.bot_manager.stop()

        logger.info("Zoom Interview Bot stopped")

    def _signal_handler(self, signum, frame):

        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_event.set()


async def main():
    setup_logging()

    logger.info("Initializing Zoom Interview Bot...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    try:
        app = ZoomInterviewBotApp()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


from .api.main import create_app
app = create_app()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted")
        sys.exit(0)
