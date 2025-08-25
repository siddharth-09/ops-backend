"""
Logging configuration for OpsFlow Guardian 2.0
"""

import logging
import logging.config
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_dir / "opsflow_guardian.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": log_dir / "errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": log_dir / "audit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
            "workflow_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": log_dir / "workflows.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            }
        },
        "loggers": {
            "": {  # root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "app.audit": {
                "level": "INFO",
                "handlers": ["audit_file"],
                "propagate": False,
            },
            "app.workflow": {
                "level": "INFO",
                "handlers": ["workflow_file", "console"],
                "propagate": False,
            },
            "portia": {
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        }
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Set up special loggers
    setup_audit_logger()
    setup_workflow_logger()


def setup_audit_logger():
    """Setup dedicated audit logger"""
    audit_logger = logging.getLogger("app.audit")
    audit_logger.info("Audit logging initialized", extra={
        "event_type": "system_startup",
        "component": "audit_logger"
    })


def setup_workflow_logger():
    """Setup dedicated workflow logger"""
    workflow_logger = logging.getLogger("app.workflow")
    workflow_logger.info("Workflow logging initialized", extra={
        "event_type": "system_startup",
        "component": "workflow_logger"
    })


def get_audit_logger():
    """Get the audit logger instance"""
    return logging.getLogger("app.audit")


def get_workflow_logger():
    """Get the workflow logger instance"""
    return logging.getLogger("app.workflow")


class StructuredLogger:
    """Structured logging helper"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(self, level: str, message: str, **kwargs):
        """Log structured event"""
        extra = {
            "event_type": kwargs.get("event_type", "general"),
            "component": kwargs.get("component", "unknown"),
            "user_id": kwargs.get("user_id"),
            "workflow_id": kwargs.get("workflow_id"),
            "agent_id": kwargs.get("agent_id"),
            **kwargs
        }
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def log_audit_event(self, event_type: str, message: str, **kwargs):
        """Log audit event"""
        audit_logger = get_audit_logger()
        extra = {
            "event_type": event_type,
            "component": "audit",
            **kwargs
        }
        audit_logger.info(message, extra=extra)
    
    def log_workflow_event(self, event_type: str, message: str, **kwargs):
        """Log workflow event"""
        workflow_logger = get_workflow_logger()
        extra = {
            "event_type": event_type,
            "component": "workflow",
            **kwargs
        }
        workflow_logger.info(message, extra=extra)
