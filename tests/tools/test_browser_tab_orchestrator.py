#!/usr/bin/env python3
"""Tests for the multi-tab browser orchestrator."""

import pytest
import time

from tools.browser_tab_orchestrator import (
    TabStatus,
    TabInfo,
    TabOrchestrator,
    get_orchestrator,
    cleanup_orchestrator,
)


class TestTabInfo:
    """Test TabInfo dataclass."""
    
    def test_tab_info_creation(self):
        """Test creating a TabInfo object."""
        tab = TabInfo(
            tab_id="test123",
            url="https://example.com",
            task_id="task_1",
        )
        assert tab.tab_id == "test123"
        assert tab.url == "https://example.com"
        assert tab.status == TabStatus.INITIALIZING
    
    def test_is_active(self):
        """Test is_active method."""
        ready_tab = TabInfo(tab_id="1", url="https://a.com", status=TabStatus.READY)
        closed_tab = TabInfo(tab_id="2", url="https://b.com", status=TabStatus.CLOSED)
        error_tab = TabInfo(tab_id="3", url="https://c.com", status=TabStatus.ERROR)
        
        assert ready_tab.is_active()
        assert not closed_tab.is_active()
        assert not error_tab.is_active()
    
    def test_age_seconds(self):
        """Test age calculation."""
        tab = TabInfo(tab_id="1", url="https://a.com")
        time.sleep(0.1)
        age = tab.age_seconds()
        assert age >= 0.1
        assert age < 0.5  # Should be close to 0.1s


class TestTabOrchestrator:
    """Test TabOrchestrator functionality."""
    
    def test_create_tab(self):
        """Test creating a new tab."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com", task_id="test")
        
        assert tab_id is not None
        assert isinstance(tab_id, str)
        
        tab = orchestrator.get_tab(tab_id)
        assert tab is not None
        assert tab.url == "https://example.com"
        assert tab.task_id == "test"
    
    def test_close_tab(self):
        """Test closing a tab."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com")
        
        success = orchestrator.close_tab(tab_id)
        assert success is True
        
        tab = orchestrator.get_tab(tab_id)
        assert tab is None
    
    def test_close_nonexistent_tab(self):
        """Test closing a tab that doesn't exist."""
        orchestrator = TabOrchestrator()
        success = orchestrator.close_tab("nonexistent")
        assert success is False
    
    def test_switch_tab(self):
        """Test switching between tabs."""
        orchestrator = TabOrchestrator()
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        # Switch to tab2
        success = orchestrator.switch_tab(tab2)
        assert success is True
        assert orchestrator.get_active_tab().tab_id == tab2
        
        # Switch to tab1
        success = orchestrator.switch_tab(tab1)
        assert success is True
        assert orchestrator.get_active_tab().tab_id == tab1
    
    def test_switch_to_nonexistent_tab(self):
        """Test switching to a tab that doesn't exist."""
        orchestrator = TabOrchestrator()
        success = orchestrator.switch_tab("nonexistent")
        assert success is False
    
    def test_switch_to_closed_tab(self):
        """Test switching to a closed tab."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com")
        orchestrator.close_tab(tab_id)
        
        success = orchestrator.switch_tab(tab_id)
        assert success is False
    
    def test_get_active_tab(self):
        """Test getting the active tab."""
        orchestrator = TabOrchestrator()
        
        # No tabs initially
        assert orchestrator.get_active_tab() is None
        
        # Create first tab - should become active
        tab1 = orchestrator.create_tab("https://a.com")
        assert orchestrator.get_active_tab().tab_id == tab1
        
        # Create second tab - first should still be active
        tab2 = orchestrator.create_tab("https://b.com")
        assert orchestrator.get_active_tab().tab_id == tab1
        
        # Switch to second
        orchestrator.switch_tab(tab2)
        assert orchestrator.get_active_tab().tab_id == tab2
    
    def test_list_tabs(self):
        """Test listing all tabs."""
        orchestrator = TabOrchestrator()
        
        # Initially empty
        tabs = orchestrator.list_tabs()
        assert len(tabs) == 0
        
        # Add tabs
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        tabs = orchestrator.list_tabs()
        assert len(tabs) == 2
        
        # Close one
        orchestrator.close_tab(tab1)
        
        tabs = orchestrator.list_tabs()
        assert len(tabs) == 1
    
    def test_list_tabs_active_only(self):
        """Test listing only active tabs."""
        orchestrator = TabOrchestrator()
        
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        # Both active
        tabs = orchestrator.list_tabs(active_only=True)
        assert len(tabs) == 2
        
        # Close one
        orchestrator.close_tab(tab1)
        
        # Only one active
        tabs = orchestrator.list_tabs(active_only=True)
        assert len(tabs) == 1
        assert tabs[0].tab_id == tab2
    
    def test_update_tab_status(self):
        """Test updating tab status."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com")
        
        success = orchestrator.update_tab_status(tab_id, TabStatus.READY)
        assert success is True
        
        tab = orchestrator.get_tab(tab_id)
        assert tab.status == TabStatus.READY
    
    def test_update_tab_status_with_title(self):
        """Test updating tab status and title."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com")
        
        success = orchestrator.update_tab_status(
            tab_id,
            TabStatus.READY,
            title="Example Domain",
        )
        assert success is True
        
        tab = orchestrator.get_tab(tab_id)
        assert tab.status == TabStatus.READY
        assert tab.title == "Example Domain"
    
    def test_update_nonexistent_tab_status(self):
        """Test updating status of nonexistent tab."""
        orchestrator = TabOrchestrator()
        success = orchestrator.update_tab_status("nonexistent", TabStatus.READY)
        assert success is False
    
    def test_max_tabs_limit(self):
        """Test that max tabs limit is enforced."""
        orchestrator = TabOrchestrator(max_tabs=3)
        
        # Create max tabs
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        tab3 = orchestrator.create_tab("https://c.com")
        
        # Should have 3 tabs
        assert len(orchestrator.list_tabs()) == 3
        
        # Create 4th - should close least recently used
        tab4 = orchestrator.create_tab("https://d.com")
        
        # Should still have 3 tabs
        assert len(orchestrator.list_tabs()) == 3
        assert tab4 in [t.tab_id for t in orchestrator.list_tabs()]
    
    def test_execute_on_tab(self):
        """Test executing a function on a specific tab."""
        orchestrator = TabOrchestrator()
        tab_id = orchestrator.create_tab("https://example.com")
        
        def test_func(x, y):
            return x + y
        
        future = orchestrator.execute_on_tab(tab_id, test_func, 5, 3)
        result = future.result(timeout=5)
        
        assert result == 8
        
        # Tab should be back to READY
        tab = orchestrator.get_tab(tab_id)
        assert tab.status == TabStatus.READY
    
    def test_execute_on_nonexistent_tab(self):
        """Test executing on a tab that doesn't exist."""
        orchestrator = TabOrchestrator()
        
        def test_func():
            return 42
        
        future = orchestrator.execute_on_tab("nonexistent", test_func)
        
        with pytest.raises(ValueError):
            future.result(timeout=5)
    
    def test_execute_on_all_tabs(self):
        """Test executing a function on all tabs."""
        orchestrator = TabOrchestrator()
        
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        def test_func():
            return 42
        
        futures = orchestrator.execute_on_all_tabs(test_func)
        
        results = orchestrator.wait_for_all(futures)
        
        assert len(results) == 2
        assert all(r == 42 for r in results.values())
    
    def test_coordinate_tabs(self):
        """Test coordinating operations across tabs."""
        orchestrator = TabOrchestrator()
        
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        def multiply(x, y):
            return x * y
        
        def add(x, y):
            return x + y
        
        operations = [
            (tab1, multiply, (5, 3), {}),
            (tab2, add, (10, 7), {}),
        ]
        
        results = orchestrator.coordinate_tabs(operations)
        
        assert results[tab1] == 15
        assert results[tab2] == 17
    
    def test_callbacks(self):
        """Test tab lifecycle callbacks."""
        orchestrator = TabOrchestrator()
        
        created_tabs = []
        closed_tabs = []
        errors = []
        
        def on_created(tab_info):
            created_tabs.append(tab_info.tab_id)
        
        def on_closed(tab_id):
            closed_tabs.append(tab_id)
        
        def on_error(tab_id, error):
            errors.append((tab_id, str(error)))
        
        orchestrator.set_callbacks(on_created, on_closed, on_error)
        
        tab_id = orchestrator.create_tab("https://example.com")
        assert tab_id in created_tabs
        
        orchestrator.close_tab(tab_id)
        assert tab_id in closed_tabs
    
    def test_cleanup(self):
        """Test cleanup of orchestrator."""
        orchestrator = TabOrchestrator()
        
        tab1 = orchestrator.create_tab("https://a.com")
        tab2 = orchestrator.create_tab("https://b.com")
        
        assert len(orchestrator.list_tabs()) == 2
        
        orchestrator.cleanup()
        
        assert len(orchestrator.list_tabs()) == 0


class TestGlobalOrchestrator:
    """Test global orchestrator management."""
    
    def test_get_orchestrator(self):
        """Test getting an orchestrator for a task."""
        orchestrator1 = get_orchestrator("task_1")
        orchestrator2 = get_orchestrator("task_1")
        
        # Should return same instance
        assert orchestrator1 is orchestrator2
        
        # Different task should get different instance
        orchestrator3 = get_orchestrator("task_2")
        assert orchestrator1 is not orchestrator3
    
    def test_cleanup_orchestrator(self):
        """Test cleaning up an orchestrator."""
        orchestrator = get_orchestrator("task_cleanup")
        orchestrator.create_tab("https://example.com")
        
        cleanup_orchestrator("task_cleanup")
        
        # Should create new instance after cleanup
        new_orchestrator = get_orchestrator("task_cleanup")
        assert orchestrator is not new_orchestrator
        assert len(new_orchestrator.list_tabs()) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_operations_list(self):
        """Test coordinate_tabs with empty operations."""
        orchestrator = TabOrchestrator()
        results = orchestrator.coordinate_tabs([])
        assert results == {}
    
    def test_operation_with_invalid_tab_id(self):
        """Test coordinate_tabs with invalid tab ID."""
        orchestrator = TabOrchestrator()
        
        def test_func():
            return 42
        
        operations = [("invalid_id", test_func, (), {})]
        results = orchestrator.coordinate_tabs(operations)
        
        # Should fail gracefully
        assert "invalid_id" in results
        assert "error" in results["invalid_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
