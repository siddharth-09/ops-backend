"""
WebSocket manager for real-time updates in OpsFlow Guardian 2.0
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections for a user"""
        if user_id in self.user_connections:
            message_text = json.dumps(message)
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message_text)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        message_text = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)


# Global connection manager instance
manager = ConnectionManager()


@websocket_router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    user_id = "dashboard-user"  # In real app, get from authentication
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial data
        await manager.send_personal_message(json.dumps({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to OpsFlow Guardian dashboard"
        }), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }), websocket)
                
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific updates
                    subscription = message.get("subscription", "")
                    await manager.send_personal_message(json.dumps({
                        "type": "subscription_confirmed",
                        "subscription": subscription,
                        "timestamp": datetime.utcnow().isoformat()
                    }), websocket)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }), websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    finally:
        manager.disconnect(websocket, user_id)


@websocket_router.websocket("/workflow/{workflow_id}")
async def websocket_workflow(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for workflow-specific updates"""
    await manager.connect(websocket)
    
    try:
        # Send workflow status
        await manager.send_personal_message(json.dumps({
            "type": "workflow_status",
            "workflow_id": workflow_id,
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), websocket)
        
        # Simulate workflow updates
        asyncio.create_task(send_workflow_updates(websocket, workflow_id))
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle workflow-specific messages
                if message.get("type") == "get_status":
                    await manager.send_personal_message(json.dumps({
                        "type": "workflow_update",
                        "workflow_id": workflow_id,
                        "status": "running",
                        "progress": 65,
                        "current_step": "Setting up development environment",
                        "timestamp": datetime.utcnow().isoformat()
                    }), websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Workflow WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Workflow {workflow_id} WebSocket disconnected")
    finally:
        manager.disconnect(websocket)


async def send_workflow_updates(websocket: WebSocket, workflow_id: str):
    """Send periodic workflow updates"""
    try:
        while True:
            await asyncio.sleep(30)  # Send updates every 30 seconds
            
            # Mock workflow progress update
            await manager.send_personal_message(json.dumps({
                "type": "workflow_progress",
                "workflow_id": workflow_id,
                "progress": 75,
                "current_step": "Finalizing setup",
                "estimated_completion": "5 minutes",
                "timestamp": datetime.utcnow().isoformat()
            }), websocket)
            
    except Exception as e:
        logger.error(f"Error sending workflow updates: {e}")


async def broadcast_system_update(update_type: str, data: Dict[str, Any]):
    """Broadcast system-wide updates"""
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(message)


async def send_agent_update(agent_id: str, status: str, metrics: Dict[str, Any] = None):
    """Send agent status update"""
    message = {
        "type": "agent_update",
        "agent_id": agent_id,
        "status": status,
        "metrics": metrics or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(message)


async def send_workflow_notification(workflow_id: str, event: str, details: Dict[str, Any] = None):
    """Send workflow event notification"""
    message = {
        "type": "workflow_notification",
        "workflow_id": workflow_id,
        "event": event,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(message)


async def send_approval_notification(approval_id: str, workflow_name: str, user_id: str = None):
    """Send approval request notification"""
    message = {
        "type": "approval_notification",
        "approval_id": approval_id,
        "workflow_name": workflow_name,
        "requires_action": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if user_id:
        await manager.send_to_user(message, user_id)
    else:
        await manager.broadcast(message)
