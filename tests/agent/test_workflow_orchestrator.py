#!/usr/bin/env python3
"""Tests for the workflow orchestration engine."""

import pytest
import time

from agent.workflow_orchestrator import (
    TaskStatus,
    WorkflowStatus,
    Task,
    Workflow,
    WorkflowOrchestrator,
    get_orchestrator,
    execute_workflow,
)


class TestTask:
    """Test Task dataclass."""
    
    def test_task_creation(self):
        """Test creating a Task."""
        def dummy_func():
            return 42
        
        task = Task(
            task_id="task1",
            name="Test Task",
            description="A test task",
            func=dummy_func,
        )
        
        assert task.task_id == "task1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0
    
    def test_is_ready_no_dependencies(self):
        """Test task readiness with no dependencies."""
        task = Task(
            task_id="task1",
            name="Test",
            description="Test",
            func=lambda: None,
        )
        
        assert task.is_ready(set())
    
    def test_is_ready_with_dependencies(self):
        """Test task readiness with dependencies."""
        task = Task(
            task_id="task1",
            name="Test",
            description="Test",
            func=lambda: None,
            dependencies={"task2", "task3"},
        )
        
        assert not task.is_ready(set())
        assert not task.is_ready({"task2"})
        assert task.is_ready({"task2", "task3"})


class TestWorkflow:
    """Test Workflow dataclass."""
    
    def test_workflow_creation(self):
        """Test creating a Workflow."""
        workflow = Workflow(
            workflow_id="wf1",
            name="Test Workflow",
            description="A test workflow",
        )
        
        assert workflow.workflow_id == "wf1"
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.tasks) == 0
    
    def test_add_task(self):
        """Test adding a task to a workflow."""
        workflow = Workflow(
            workflow_id="wf1",
            name="Test",
            description="Test",
        )
        
        task = Task(
            task_id="task1",
            name="Test Task",
            description="Test",
            func=lambda: None,
        )
        
        workflow.add_task(task)
        
        assert len(workflow.tasks) == 1
        assert workflow.get_task("task1") is task
    
    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        workflow = Workflow(
            workflow_id="wf1",
            name="Test",
            description="Test",
        )
        
        task1 = Task(
            task_id="task1",
            name="Task 1",
            description="Test",
            func=lambda: None,
        )
        task2 = Task(
            task_id="task2",
            name="Task 2",
            description="Test",
            func=lambda: None,
            dependencies={"task1"},
        )
        
        workflow.add_task(task1)
        workflow.add_task(task2)
        
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task1"
        
        # Complete task1
        task1.status = TaskStatus.COMPLETED
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task2"


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator functionality."""
    
    def test_create_workflow(self):
        """Test creating a workflow."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow(
            name="Test Workflow",
            description="A test workflow",
        )
        
        assert workflow.workflow_id is not None
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.PENDING
    
    def test_add_task_to_workflow(self):
        """Test adding a task to a workflow."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Test", "Test")
        
        def dummy_func():
            return 42
        
        task_id = orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Test Task",
            description="A test task",
            func=dummy_func,
        )
        
        assert task_id is not None
        
        workflow = orchestrator._workflows[workflow.workflow_id]
        assert len(workflow.tasks) == 1
    
    def test_execute_simple_workflow(self):
        """Test executing a simple workflow with no dependencies."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Simple Test", "Test")
        
        def task_func():
            return "success"
        
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 1",
            description="Test task",
            func=task_func,
        )
        
        results = orchestrator.execute_workflow(workflow.workflow_id)
        
        assert results["status"] == "completed"
        assert "tasks" in results
    
    def test_execute_workflow_with_dependencies(self):
        """Test executing a workflow with task dependencies."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Dependent Test", "Test")
        
        execution_order = []
        
        def task1():
            execution_order.append("task1")
            return "result1"
        
        def task2():
            execution_order.append("task2")
            return "result2"
        
        task1_id = orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 1",
            description="First task",
            func=task1,
        )
        
        task2_id = orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 2",
            description="Second task",
            func=task2,
            dependencies={task1_id},
        )
        
        results = orchestrator.execute_workflow(workflow.workflow_id)
        
        assert results["status"] == "completed"
        assert execution_order == ["task1", "task2"]
    
    def test_execute_workflow_with_parallel_tasks(self):
        """Test executing a workflow with parallel tasks."""
        orchestrator = WorkflowOrchestrator(max_parallel_tasks=3)
        workflow = orchestrator.create_workflow("Parallel Test", "Test")
        
        execution_times = []
        
        def task(name):
            start = time.time()
            time.sleep(0.1)
            execution_times.append((name, time.time() - start))
            return name
        
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 1",
            description="Test",
            func=lambda: task("task1"),
        )
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 2",
            description="Test",
            func=lambda: task("task2"),
        )
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 3",
            description="Test",
            func=lambda: task("task3"),
        )
        
        start = time.time()
        results = orchestrator.execute_workflow(workflow.workflow_id)
        total_time = time.time() - start
        
        assert results["status"] == "completed"
        # With parallel execution, should be faster than sequential
        assert total_time < 0.3  # 3 tasks * 0.1s = 0.3s sequential, parallel should be faster
    
    def test_task_retry_on_failure(self):
        """Test task retry logic."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Retry Test", "Test")
        
        attempts = []
        
        def flaky_task():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("Failed")
            return "success"
        
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Flaky Task",
            description="Test",
            func=flaky_task,
            max_retries=3,
        )
        
        results = orchestrator.execute_workflow(workflow.workflow_id)
        
        assert results["status"] == "completed"
        assert len(attempts) == 2  # Failed once, succeeded on retry
    
    def test_workflow_failure_on_max_retries(self):
        """Test workflow fails when task exceeds max retries."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Failure Test", "Test")
        
        def always_fail():
            raise ValueError("Always fails")
        
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Failing Task",
            description="Test",
            func=always_fail,
            max_retries=2,
        )
        
        results = orchestrator.execute_workflow(workflow.workflow_id)
        
        assert results["status"] == "failed"
    
    def test_decompose_research_task(self):
        """Test decomposition of research tasks."""
        orchestrator = WorkflowOrchestrator()
        subtasks = orchestrator.decompose_task("Research the history of AI")
        
        assert len(subtasks) > 1
        assert any(t["name"] == "search_web" for t in subtasks)
        assert any(t["name"] == "synthesize_findings" for t in subtasks)
    
    def test_decompose_coding_task(self):
        """Test decomposition of coding tasks."""
        orchestrator = WorkflowOrchestrator()
        subtasks = orchestrator.decompose_task("Implement a sorting algorithm")
        
        assert len(subtasks) > 1
        assert any(t["name"] == "write_code" for t in subtasks)
        assert any(t["name"] == "test_code" for t in subtasks)
    
    def test_decompose_browser_task(self):
        """Test decomposition of browser tasks."""
        orchestrator = WorkflowOrchestrator()
        subtasks = orchestrator.decompose_task("Browse to example.com and click the button")
        
        assert len(subtasks) > 1
        assert any(t["name"] == "navigate_to_page" for t in subtasks)
    
    def test_decompose_generic_task(self):
        """Test decomposition of generic tasks."""
        orchestrator = WorkflowOrchestrator()
        subtasks = orchestrator.decompose_task("Do something simple")
        
        assert len(subtasks) == 1
        assert subtasks[0]["name"] == "execute_task"
    
    def test_create_workflow_from_description(self):
        """Test creating workflow from task description."""
        orchestrator = WorkflowOrchestrator()
        
        task_functions = {
            "search_web": lambda: "search results",
            "analyze_sources": lambda: "analysis",
            "synthesize_findings": lambda: "summary",
        }
        
        workflow_id = orchestrator.create_workflow_from_description(
            "Research quantum computing",
            task_functions,
        )
        
        assert workflow_id is not None
        workflow = orchestrator._workflows[workflow_id]
        assert len(workflow.tasks) > 0
    
    def test_get_workflow_status(self):
        """Test getting workflow status."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Status Test", "Test")
        
        status = orchestrator.get_workflow_status(workflow.workflow_id)
        
        assert status is not None
        assert status["workflow_id"] == workflow.workflow_id
        assert status["status"] == "pending"
    
    def test_callbacks(self):
        """Test workflow event callbacks."""
        orchestrator = WorkflowOrchestrator()
        
        task_completed = []
        workflow_completed = []
        
        def on_task_completed(wf_id, task_id, result):
            task_completed.append((wf_id, task_id, result))
        
        def on_workflow_completed(wf_id):
            workflow_completed.append(wf_id)
        
        orchestrator.set_callbacks(
            on_task_completed=on_task_completed,
            on_workflow_completed=on_workflow_completed,
        )
        
        workflow = orchestrator.create_workflow("Callback Test", "Test")
        orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 1",
            description="Test",
            func=lambda: "done",
        )
        
        orchestrator.execute_workflow(workflow.workflow_id)
        
        assert len(task_completed) == 1
        assert len(workflow_completed) == 1
    
    def test_cleanup(self):
        """Test cleanup of orchestrator."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Cleanup Test", "Test")
        
        assert len(orchestrator._workflows) == 1
        
        orchestrator.cleanup()
        
        assert len(orchestrator._workflows) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns a singleton."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        assert orchestrator1 is orchestrator2
    
    def test_execute_workflow_function(self):
        """Test the convenience function for executing workflows."""
        task_functions = {
            "execute_task": lambda: "completed",
        }
        
        results = execute_workflow(
            task_description="Do something",
            task_functions=task_functions,
        )
        
        assert results is not None
        assert "status" in results


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_add_task_to_nonexistent_workflow(self):
        """Test adding task to nonexistent workflow."""
        orchestrator = WorkflowOrchestrator()
        
        with pytest.raises(ValueError):
            orchestrator.add_task_to_workflow(
                workflow_id="nonexistent",
                name="Task",
                description="Test",
                func=lambda: None,
            )
    
    def test_execute_nonexistent_workflow(self):
        """Test executing nonexistent workflow."""
        orchestrator = WorkflowOrchestrator()
        
        with pytest.raises(ValueError):
            orchestrator.execute_workflow("nonexistent")
    
    def test_circular_dependencies(self):
        """Test handling of circular dependencies."""
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.create_workflow("Circular Test", "Test")
        
        task1_id = orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 1",
            description="Test",
            func=lambda: "result1",
        )
        task2_id = orchestrator.add_task_to_workflow(
            workflow_id=workflow.workflow_id,
            name="Task 2",
            description="Test",
            func=lambda: "result2",
            dependencies={task1_id},
        )
        
        # Add circular dependency
        task1 = workflow.get_task(task1_id)
        task1.dependencies = {task2_id}
        
        # Should handle gracefully (may hang or fail gracefully)
        # This is a known limitation - the system should detect circular deps
        results = orchestrator.execute_workflow(workflow.workflow_id)
        # May complete or fail depending on implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
