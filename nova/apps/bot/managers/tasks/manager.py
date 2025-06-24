from discord.ext import tasks
from typing import TYPE_CHECKING

from .tasklist import TaskList

from ...log import Logger
from ...conf import conf

if TYPE_CHECKING:
    from ...client import Client

logger = Logger.TASKS


class TaskManager:
    def __init__(self, client: "Client") -> None:
        self.client = client
        self.tasklist = TaskList(client)
    
    async def start(self) -> None:
        logger.info("Starting tasks")
        
        for taskname in conf.tasks:
            task = getattr(self.tasklist, taskname, None)
            
            if callable(task) and isinstance(task, tasks.Loop):
                if not task.is_running():
                    task.start()
                    logger.info(f"Started task '{taskname}'")
                else:
                    logger.info(f"Task '{taskname}' is already running")
            else:
                logger.error(f"Task '{taskname}' is not a valid task or is not callable")
                continue
        
        logger.info("Tasks started")

    async def stop(self) -> None:        
        for taskname in conf.tasks:
            task = getattr(self.tasklist, taskname, None)
            
            if callable(task) and isinstance(task, tasks.Loop):
                if task.is_running():
                    task.stop()
                    logger.info(f"Stopped task {taskname}")
                else:
                    logger.info(f"Task {taskname} is not running")
            else:
                logger.warning(f"Task {taskname} is not a valid task or is not callable")
                continue
    
    async def cancel_all_tasks(self) -> None:
        logger.info("Cancelling all tasks")
        
        await self.stop()
        
        for attr_name in dir(self.tasklist):
            task = getattr(self.tasklist, attr_name, None)
            
            if callable(task) and isinstance(task, tasks.Loop):
                try:
                    if task.is_running():
                        task.cancel()
                except Exception as e:
                    logger.error(f"Error cancelling task '{attr_name}': {e}")
        
        logger.info("All tasks cancelled")