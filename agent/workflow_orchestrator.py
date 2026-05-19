#!/usr/bin/env python3
"""
Workflow Orchestration Engine

Decomposes complex tasks into subtasks, executes them with dependencies,
and coordinates parallel execution. Inspired by Perplexity Computer's
workflow orchestration capabilities.

Features:
- Task decomposition into subtasks
- Dependency management between subtasks
- Parallel execution of independent subtasks
- State tracking and progress reporting
- Error handling and retry logic
- Workflow templates for common patterns
"""

import asyncio
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Status of a workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A single task in a workflow."""
    task_id: str
    name: str
    description: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to run (all dependencies completed)."""
        return self.dependencies.issubset(completed_tasks)


@dataclass
class Workflow:
    """A workflow composed of multiple tasks."""
    workflow_id: str
    name: str
    description: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self.tasks[task.task_id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run."""
        completed = {tid for tid, t in self.tasks.items() if t.status == TaskStatus.COMPLETED}
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING and t.is_ready(completed)]


class WorkflowOrchestrator:
    """
    Orchestrates complex workflows with task decomposition and dependency management.
    
    Automatically decomposes tasks, manages dependencies, executes in parallel
    where possible, and tracks progress.
    """
    
    def __init__(self, max_parallel_tasks: int = 5):
        """
        Initialize the workflow orchestrator.
        
        Args:
            max_parallel_tasks: Maximum number of tasks to run in parallel
        """
        self.max_parallel_tasks = max_parallel_tasks
        self._workflows: Dict[str, Workflow] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_parallel_tasks)
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_task_completed: Optional[Callable[[str, str, Any], None]] = None
        self._on_task_failed: Optional[Callable[[str, str, Exception], None]] = None
        self._on_workflow_completed: Optional[Callable[[str], None]] = None
        self._on_workflow_failed: Optional[Callable[[str, str], None]] = None
    
    def create_workflow(
        self,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
            metadata: Optional metadata
        
        Returns:
            Workflow instance
        """
        workflow = Workflow(
            workflow_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            metadata=metadata or {},
        )
        
        with self._lock:
            self._workflows[workflow.workflow_id] = workflow
        
        return workflow
    
    def add_task_to_workflow(
        self,
        workflow_id: str,
        name: str,
        description: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        dependencies: Set[str] = None,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Add a task to a workflow.
        
        Args:
            workflow_id: Workflow ID
            name: Task name
            description: Task description
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            dependencies: Set of task IDs this task depends on
            max_retries: Maximum retry attempts
            timeout: Timeout in seconds
            metadata: Optional metadata
        
        Returns:
            Task ID
        """
        with self._lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            task = Task(
                task_id=str(uuid.uuid4())[:8],
                name=name,
                description=description,
                func=func,
                args=args,
                kwargs=kwargs or {},
                dependencies=dependencies or set(),
                max_retries=max_retries,
                timeout=timeout,
                metadata=metadata or {},
            )
            
            workflow.add_task(task)
            return task.task_id
    
    def execute_workflow(
        self,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Execute a workflow with dependency management and parallel execution.
        
        Args:
            workflow_id: Workflow ID to execute
        
        Returns:
            Dict with workflow results
        """
        with self._lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = time.time()
        
        completed_tasks = set()
        failed_tasks = set()
        
        try:
            while len(completed_tasks) + len(failed_tasks) < len(workflow.tasks):
                # Get ready tasks
                ready_tasks = workflow.get_ready_tasks()
                
                if not ready_tasks:
                    # Check if we have failed tasks blocking progress
                    if failed_tasks:
                        raise RuntimeError(f"Workflow failed: {len(failed_tasks)} tasks failed")
                    # Circular dependency or no progress
                    break
                
                # Execute ready tasks in parallel (up to max_parallel_tasks)
                batch = ready_tasks[:self.max_parallel_tasks]
                futures = {}
                
                for task in batch:
                    task.status = TaskStatus.RUNNING
                    future = self._executor.submit(self._execute_task, task)
                    futures[future] = task
                
                # Wait for batch to complete
                for future, task in futures.items():
                    try:
                        result = future.result(timeout=task.timeout)
                        task.result = result
                        task.status = TaskStatus.COMPLETED
                        completed_tasks.add(task.task_id)
                        
                        if self._on_task_completed:
                            try:
                                self._on_task_completed(workflow_id, task.task_id, result)
                            except Exception as e:
                                logger.warning(f"Task completed callback failed: {e}")
                    
                    except Exception as e:
                        task.error = str(e)
                        task.retry_count += 1
                        
                        if task.retry_count < task.max_retries:
                            task.status = TaskStatus.PENDING
                            logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
                        else:
                            task.status = TaskStatus.FAILED
                            failed_tasks.add(task.task_id)
                            
                            if self._on_task_failed:
                                try:
                                    self._on_task_failed(workflow_id, task.task_id, e)
                                except Exception as cb_err:
                                    logger.warning(f"Task failed callback failed: {cb_err}")
            
            # Determine final status
            if failed_tasks:
                workflow.status = WorkflowStatus.FAILED
                if self._on_workflow_failed:
                    try:
                        self._on_workflow_failed(workflow_id, f"{len(failed_tasks)} tasks failed")
                    except Exception as e:
                        logger.warning(f"Workflow failed callback failed: {e}")
            else:
                workflow.status = WorkflowStatus.COMPLETED
                if self._on_workflow_completed:
                    try:
                        self._on_workflow_completed(workflow_id)
                    except Exception as e:
                        logger.warning(f"Workflow completed callback failed: {e}")
        
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.error(f"Workflow execution failed: {e}")
            raise
        
        finally:
            workflow.completed_at = time.time()
        
        return self._get_workflow_results(workflow)
    
    def _execute_task(self, task: Task) -> Any:
        """Execute a single task."""
        return task.func(*task.args, **task.kwargs)
    
    def _get_workflow_results(self, workflow: Workflow) -> Dict[str, Any]:
        """Get results from a workflow."""
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "duration_seconds": (workflow.completed_at or time.time()) - (workflow.started_at or workflow.created_at),
            "tasks": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                }
                for task_id, task in workflow.tasks.items()
            },
        }
    
    def decompose_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Decompose a complex task into subtasks using LLM assistance.
        
        Args:
            task_description: The complex task to decompose
            context: Additional context for decomposition
        
        Returns:
            List of subtask definitions
        """
        # Simple rule-based decomposition for common patterns
        subtasks = []
        
        # Research pattern
        if any(kw in task_description.lower() for kw in ["research", "investigate", "find information about"]):
            subtasks.extend([
                {
                    "name": "search_web",
                    "description": f"Search the web for information about: {task_description}",
                    "dependencies": set(),
                },
                {
                    "name": "analyze_sources",
                    "description": "Analyze and evaluate the credibility of sources",
                    "dependencies": {"search_web"},
                },
                {
                    "name": "synthesize_findings",
                    "description": "Synthesize findings into a coherent summary",
                    "dependencies": {"analyze_sources"},
                },
            ])
        
        # Coding pattern
        elif any(kw in task_description.lower() for kw in ["implement", "write code", "create a function"]):
            subtasks.extend([
                {
                    "name": "analyze_requirements",
                    "description": "Analyze requirements and design the solution",
                    "dependencies": set(),
                },
                {
                    "name": "write_code",
                    "description": "Write the implementation",
                    "dependencies": {"analyze_requirements"},
                },
                {
                    "name": "test_code",
                    "description": "Test the implementation",
                    "dependencies": {"write_code"},
                },
                {
                    "name": "document_code",
                    "description": "Add documentation",
                    "dependencies": {"test_code"},
                },
            ])
        
        # Browser automation pattern
        elif any(kw in task_description.lower() for kw in ["browse", "navigate", "click through"]):
            subtasks.extend([
                {
                    "name": "navigate_to_page",
                    "description": "Navigate to the target page",
                    "dependencies": set(),
                },
                {
                    "name": "interact_with_elements",
                    "description": "Interact with page elements",
                    "dependencies": {"navigate_to_page"},
                },
                {
                    "name": "extract_information",
                    "description": "Extract required information",
                    "dependencies": {"interact_with_elements"},
                },
            ])
        
        # Default: single task
        else:
            subtasks.append({
                "name": "execute_task",
                "description": task_description,
                "dependencies": set(),
            })
        
        return subtasks
    
    def create_workflow_from_description(
        self,
        task_description: str,
        task_functions: Dict[str, Callable],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a workflow from a task description by decomposing it.
        
        Args:
            task_description: The task to decompose and execute
            task_functions: Mapping of task names to functions
            context: Additional context
        
        Returns:
            Workflow ID
        """
        subtasks = self.decompose_task(task_description, context)
        
        workflow = self.create_workflow(
            name=f"Auto-generated: {task_description[:50]}",
            description=task_description,
            metadata={"auto_generated": True},
        )
        
        # Build dependency mapping
        task_id_map = {}
        for subtask in subtasks:
            task_id = self.add_task_to_workflow(
                workflow_id=workflow.workflow_id,
                name=subtask["name"],
                description=subtask["description"],
                func=task_functions.get(subtask["name"], lambda: None),
                dependencies=subtask["dependencies"],
            )
            task_id_map[subtask["name"]] = task_id
        
        # Update dependencies to use task IDs
        for subtask in subtasks:
            task = workflow.get_task(task_id_map[subtask["name"]])
            if task:
                task.dependencies = {task_id_map[dep] for dep in subtask["dependencies"]}
        
        return workflow.workflow_id
    
    def set_callbacks(
        self,
        on_task_completed: Optional[Callable[[str, str, Any], None]] = None,
        on_task_failed: Optional[Callable[[str, str, Exception], None]] = None,
        on_workflow_completed: Optional[Callable[[str], None]] = None,
        on_workflow_failed: Optional[Callable[[str, str], None]] = None,
    ):
        """Set workflow event callbacks."""
        self._on_task_completed = on_task_completed
        self._on_task_failed = on_task_failed
        self._on_workflow_completed = on_workflow_completed
        self._on_workflow_failed = on_workflow_failed
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow."""
        with self._lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                return None
            
            return {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "status": workflow.status.value,
                "total_tasks": len(workflow.tasks),
                "completed_tasks": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETED),
                "failed_tasks": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.FAILED),
                "pending_tasks": sum(1 for t in workflow.tasks.values() if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)),
            }
    
    def cleanup(self, workflow_id: Optional[str] = None):
        """Clean up workflow(s)."""
        with self._lock:
            if workflow_id:
                self._workflows.pop(workflow_id, None)
            else:
                self._workflows.clear()
        
        self._executor.shutdown(wait=True)


# Global orchestrator instance
_default_orchestrator: Optional[WorkflowOrchestrator] = None


def get_orchestrator(max_parallel_tasks: int = 5) -> WorkflowOrchestrator:
    """Get the default workflow orchestrator instance."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = WorkflowOrchestrator(max_parallel_tasks)
    return _default_orchestrator


def execute_workflow(
    task_description: str,
    task_functions: Dict[str, Callable],
    context: Optional[Dict[str, Any]] = None,
    max_parallel_tasks: int = 5,
) -> Dict[str, Any]:
    """
    Convenience function to execute a workflow from a task description.
    
    Args:
        task_description: The task to execute
        task_functions: Mapping of task names to functions
        context: Additional context
        max_parallel_tasks: Maximum parallel tasks
    
    Returns:
        Workflow execution results
    """
    orchestrator = WorkflowOrchestrator(max_parallel_tasks=max_parallel_tasks)
    workflow_id = orchestrator.create_workflow_from_description(
        task_description,
        task_functions,
        context,
    )
    return orchestrator.execute_workflow(workflow_id)
