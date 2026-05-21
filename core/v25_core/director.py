"""
ARP v25 - Director Module
Goal assignment and task distribution
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TaskPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class ResearchGoal:
    """A research goal to be accomplished"""
    id: str
    target: str
    disease: str
    priority: TaskPriority
    description: str
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []

class Director:
    """
    Main orchestrator for research goals.
    Assigns tasks to appropriate agents based on goals.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.goals: Dict[str, ResearchGoal] = {}
        self.task_history: List[Dict] = []
        
    def add_goal(self, goal: ResearchGoal) -> str:
        """Add a research goal"""
        self.goals[goal.id] = goal
        return goal.id
    
    def create_goal(
        self,
        target: str,
        disease: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        description: str = "",
        constraints: List[str] = None
    ) -> str:
        """Create and add a new research goal"""
        import uuid
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        goal = ResearchGoal(
            id=goal_id,
            target=target,
            disease=disease,
            priority=priority,
            description=description,
            constraints=constraints or []
        )
        return self.add_goal(goal)
    
    def get_next_task(self, agent_id: str) -> Optional[ResearchGoal]:
        """Get next task for an agent based on priority"""
        pending = [g for g in self.goals.values() 
                   if g.priority == TaskPriority.HIGH]
        if pending:
            return pending[0]
        
        pending = [g for g in self.goals.values() 
                   if g.priority == TaskPriority.MEDIUM]
        if pending:
            return pending[0]
        
        return None
    
    def complete_task(self, goal_id: str, result: Any):
        """Mark a task as completed"""
        if goal_id in self.goals:
            self.task_history.append({
                "goal_id": goal_id,
                "result": result,
                "status": "completed"
            })
            del self.goals[goal_id]
    
    def get_status(self) -> Dict:
        """Get current status of all goals"""
        return {
            "total_goals": len(self.goals),
            "high_priority": len([g for g in self.goals.values() 
                                if g.priority == TaskPriority.HIGH]),
            "completed_tasks": len(self.task_history),
            "pending": [
                {"id": g.id, "target": g.target, "disease": g.disease}
                for g in self.goals.values()
            ]
        }
