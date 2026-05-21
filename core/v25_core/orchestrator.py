"""
ARP v25 - Orchestrator Module
Coordinates routing and execution of tasks
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """A task to be executed"""
    id: str
    task_type: str
    payload: Dict[str, Any]
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None

class Orchestrator:
    """
    Main orchestrator that coordinates task execution.
    Routes tasks to appropriate handlers.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.handlers: Dict[str, Callable] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type"""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for: {task_type}")
    
    def create_task(self, task_type: str, payload: Dict) -> str:
        """Create a new task"""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            task_type=task_type,
            payload=payload
        )
        self.tasks[task_id] = task
        self.task_queue.append(task)
        return task_id
    
    async def execute_task(self, task_id: str) -> Any:
        """Execute a task using the registered handler"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        handler = self.handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"No handler for task type: {task.task_type}")
        
        try:
            task.status = "running"
            result = await handler(task.payload)
            task.result = result
            task.status = "completed"
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Task {task_id} failed: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get status of a task"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        return {
            "id": task.id,
            "type": task.task_type,
            "status": task.status,
            "result": task.result,
            "error": task.error
        }
    
    def get_queue_status(self) -> Dict:
        """Get queue status"""
        return {
            "total": len(self.tasks),
            "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
            "running": len([t for t in self.tasks.values() if t.status == "running"]),
            "completed": len([t for t in self.tasks.values() if t.status == "completed"]),
            "failed": len([t for t in self.tasks.values() if t.status == "failed"]),
        }
