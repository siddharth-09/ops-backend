"""
Agent models for OpsFlow Guardian 2.0
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class AgentRole(str, Enum):
    """Agent role types"""
    PLANNER = "planner"
    EXECUTOR = "executor"
    AUDITOR = "auditor"
    MONITOR = "monitor"


class AgentStatus(str, Enum):
    """Agent status types"""
    ACTIVE = "active"
    WORKING = "working"
    IDLE = "idle"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Agent(BaseModel):
    """Agent model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    total_tasks_completed: int = 0
    success_rate: float = 0.0
    current_task_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    last_error: Optional[str] = None
    uptime_percentage: float = 100.0
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 0.0
        return (self.tasks_completed / total_tasks) * 100.0


class AgentTask(BaseModel):
    """Task assigned to an agent"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    task_type: str
    description: str
    status: str = "pending"
    priority: str = "medium"
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentCommunication(BaseModel):
    """Inter-agent communication message"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent_id: str
    to_agent_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
