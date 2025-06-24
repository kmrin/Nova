import os
import sys
import atexit
import signal
import asyncio
import threading

from django.apps import AppConfig

from .log import Logger

RUN_BOT = os.getenv("BOT_RUN_WITH_DJANGO", "False").lower() == "true"

logger = Logger.CLIENT


class NovaConfig(AppConfig):
    name = "apps.bot"
    verbose_name = "Nova Discord Bot"
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    bot_loop: asyncio.AbstractEventLoop | None = None
    bot_thread: threading.Thread | None = None
    client = None
    
    def ready(self) -> None:
        if (
            (threading.current_thread() is not threading.main_thread()) or
            (NovaConfig.bot_thread is not None and NovaConfig.bot_thread.is_alive()) or
            (NovaConfig.client is not None) or
            not RUN_BOT
        ):
            logger.info("Skipping bot setup")
            return
        
        def run() -> None:
            from .client import Client
            
            NovaConfig.bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(NovaConfig.bot_loop)
            
            NovaConfig.client = Client()
            NovaConfig.bot_loop.run_until_complete(NovaConfig.client.init())
        
        def stop(*args, **kwargs) -> None:
            logger.info("Received shutdown signal")
            
            if NovaConfig.client and NovaConfig.bot_loop:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        NovaConfig.client.stop(),
                        NovaConfig.bot_loop
                    )
                    
                    future.result(timeout=20)
                    logger.info("Bye!")
                
                except Exception as _:
                    # TODO: Figure out the unknown error happening during shutdown, but for now it seems harmless
                    pass
                
                finally:
                    if NovaConfig.bot_loop and NovaConfig.bot_loop.is_running():
                        NovaConfig.bot_loop.stop()
                        NovaConfig.bot_loop.close()
                        NovaConfig.bot_loop = None
        
        atexit.register(stop)
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        
        NovaConfig.bot_thread = threading.Thread(target=run, daemon=True)
        NovaConfig.bot_thread.start()