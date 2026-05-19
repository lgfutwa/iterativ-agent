#!/usr/bin/env python3
"""
Multi-Tab Browser Orchestration System

Provides native multi-tab orchestration for browser automation, similar to
Perplexity Computer's browser agent capabilities. Enables parallel operations
across tabs, tab coordination, and intelligent tab management.

Features:
- Tab lifecycle management (create, switch, close)
- Parallel operations across multiple tabs
- Tab coordination and synchronization
- Tab state tracking and persistence
- Integration with existing browser tools
"""

import asyncio
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from functools import wraps

logger = logging.getLogger(__name__)


class TabStatus(Enum):
    """Status of a browser tab."""
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    BUSY = "busy"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class TabInfo:
    """Information about a browser tab."""
    tab_id: str
    url: str
    title: str = ""
    status: TabStatus = TabStatus.INITIALIZING
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if tab is active (not closed or in error)."""
        return self.status not in (TabStatus.CLOSED, TabStatus.ERROR)
    
    def age_seconds(self) -> float:
        """Get age of tab in seconds."""
        return time.time() - self.created_at


class TabOrchestrator:
    """
    Orchestrates multiple browser tabs for parallel operations.
    
    Manages tab lifecycle, coordinates operations across tabs, and provides
    synchronization primitives for complex multi-tab workflows.
    """
    
    def __init__(self, max_tabs: int = 10, max_concurrent_ops: int = 5):
        """
        Initialize the tab orchestrator.
        
        Args:
            max_tabs: Maximum number of tabs allowed
            max_concurrent_ops: Maximum parallel operations across tabs
        """
        self.max_tabs = max_tabs
        self.max_concurrent_ops = max_concurrent_ops
        
        # Tab storage
        self._tabs: Dict[str, TabInfo] = {}
        self._active_tab_id: Optional[str] = None
        self._tab_lock = threading.RLock()
        
        # Operation executor for parallel tab operations
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_ops)
        
        # Callbacks for tab events
        self._on_tab_created: Optional[Callable[[TabInfo], None]] = None
        self._on_tab_closed: Optional[Callable[[str], None]] = None
        self._on_tab_error: Optional[Callable[[str, Exception], None]] = None
    
    def create_tab(
        self,
        url: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new browser tab.
        
        Args:
            url: Initial URL for the tab
            task_id: Associated task ID
            metadata: Optional metadata for the tab
        
        Returns:
            Tab ID of the new tab
        """
        with self._tab_lock:
            # Check tab limit
            if len(self._tabs) >= self.max_tabs:
                # Close least recently used tab
                self._close_least_recently_used_tab()
            
            # Generate tab ID
            tab_id = str(uuid.uuid4())[:8]
            
            # Create tab info
            tab_info = TabInfo(
                tab_id=tab_id,
                url=url,
                task_id=task_id,
                metadata=metadata or {},
                status=TabStatus.INITIALIZING,
            )
            
            self._tabs[tab_id] = tab_info
            
            # Set as active if it's the first tab
            if self._active_tab_id is None:
                self._active_tab_id = tab_id
            
            logger.info(f"Created tab {tab_id} for URL: {url}")
            
            # Notify callback
            if self._on_tab_created:
                try:
                    self._on_tab_created(tab_info)
                except Exception as e:
                    logger.warning(f"Tab created callback failed: {e}")
            
            return tab_id
    
    def close_tab(self, tab_id: str) -> bool:
        """
        Close a browser tab.
        
        Args:
            tab_id: ID of the tab to close
        
        Returns:
            True if tab was closed, False if tab didn't exist
        """
        with self._tab_lock:
            if tab_id not in self._tabs:
                return False
            
            tab_info = self._tabs[tab_id]
            tab_info.status = TabStatus.CLOSED
            
            # If this was the active tab, switch to another
            if self._active_tab_id == tab_id:
                self._switch_to_another_tab()
            
            del self._tabs[tab_id]
            
            logger.info(f"Closed tab {tab_id}")
            
            # Notify callback
            if self._on_tab_closed:
                try:
                    self._on_tab_closed(tab_id)
                except Exception as e:
                    logger.warning(f"Tab closed callback failed: {e}")
            
            return True
    
    def switch_tab(self, tab_id: str) -> bool:
        """
        Switch to a different tab.
        
        Args:
            tab_id: ID of the tab to switch to
        
        Returns:
            True if switched successfully, False otherwise
        """
        with self._tab_lock:
            if tab_id not in self._tabs:
                return False
            
            if not self._tabs[tab_id].is_active():
                return False
            
            self._active_tab_id = tab_id
            self._tabs[tab_id].last_active = time.time()
            
            logger.info(f"Switched to tab {tab_id}")
            return True
    
    def get_active_tab(self) -> Optional[TabInfo]:
        """Get the currently active tab."""
        with self._tab_lock:
            if self._active_tab_id is None:
                return None
            return self._tabs.get(self._active_tab_id)
    
    def get_tab(self, tab_id: str) -> Optional[TabInfo]:
        """Get information about a specific tab."""
        with self._tab_lock:
            return self._tabs.get(tab_id)
    
    def list_tabs(self, active_only: bool = False) -> List[TabInfo]:
        """
        List all tabs.
        
        Args:
            active_only: If True, only return active tabs
        
        Returns:
            List of tab information
        """
        with self._tab_lock:
            tabs = list(self._tabs.values())
            if active_only:
                tabs = [t for t in tabs if t.is_active()]
            return tabs
    
    def update_tab_status(
        self,
        tab_id: str,
        status: TabStatus,
        title: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a tab.
        
        Args:
            tab_id: ID of the tab
            status: New status
            title: Optional new title
        
        Returns:
            True if updated, False if tab doesn't exist
        """
        with self._tab_lock:
            if tab_id not in self._tabs:
                return False
            
            self._tabs[tab_id].status = status
            if title is not None:
                self._tabs[tab_id].title = title
            
            return True
    
    def execute_on_tab(
        self,
        tab_id: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Future:
        """
        Execute a function on a specific tab in parallel.
        
        Args:
            tab_id: ID of the tab to execute on
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            Future for the operation
        """
        def wrapped():
            try:
                with self._tab_lock:
                    if tab_id not in self._tabs:
                        raise ValueError(f"Tab {tab_id} not found")
                    
                    self._tabs[tab_id].status = TabStatus.BUSY
                    self._tabs[tab_id].last_active = time.time()
                
                result = func(*args, **kwargs)
                
                with self._tab_lock:
                    if tab_id in self._tabs:
                        self._tabs[tab_id].status = TabStatus.READY
                
                return result
            except Exception as e:
                with self._tab_lock:
                    if tab_id in self._tabs:
                        self._tabs[tab_id].status = TabStatus.ERROR
                
                logger.error(f"Error executing on tab {tab_id}: {e}")
                
                # Notify error callback
                if self._on_tab_error:
                    try:
                        self._on_tab_error(tab_id, e)
                    except Exception as cb_err:
                        logger.warning(f"Tab error callback failed: {cb_err}")
                
                raise
        
        return self._executor.submit(wrapped)
    
    def execute_on_all_tabs(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Dict[str, Future]:
        """
        Execute a function on all active tabs in parallel.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            Dictionary mapping tab IDs to Futures
        """
        futures = {}
        for tab in self.list_tabs(active_only=True):
            futures[tab.tab_id] = self.execute_on_tab(tab.tab_id, func, *args, **kwargs)
        return futures
    
    def wait_for_all(self, futures: Dict[str, Future], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for all futures to complete.
        
        Args:
            futures: Dictionary of tab IDs to Futures
            timeout: Optional timeout in seconds
        
        Returns:
            Dictionary mapping tab IDs to results
        """
        results = {}
        for tab_id, future in futures.items():
            try:
                results[tab_id] = future.result(timeout=timeout)
            except Exception as e:
                results[tab_id] = {"error": str(e)}
        return results
    
    def coordinate_tabs(
        self,
        operations: List[Tuple[str, Callable, tuple, dict]],
    ) -> Dict[str, Any]:
        """
        Coordinate operations across multiple tabs.
        
        Args:
            operations: List of (tab_id, func, args, kwargs) tuples
        
        Returns:
            Dictionary mapping tab IDs to results
        """
        futures = {}
        for tab_id, func, args, kwargs in operations:
            futures[tab_id] = self.execute_on_tab(tab_id, func, *args, **kwargs)
        
        return self.wait_for_all(futures)
    
    def _switch_to_another_tab(self):
        """Switch to another available tab."""
        active_tabs = [t for t in self._tabs.values() if t.is_active()]
        if active_tabs:
            # Switch to most recently active
            self._active_tab_id = max(active_tabs, key=lambda t: t.last_active).tab_id
        else:
            self._active_tab_id = None
    
    def _close_least_recently_used_tab(self):
        """Close the least recently used tab."""
        active_tabs = [t for t in self._tabs.values() if t.is_active()]
        if not active_tabs:
            return
        
        # Close least recently used
        lru_tab = min(active_tabs, key=lambda t: t.last_active)
        self.close_tab(lru_tab.tab_id)
    
    def set_callbacks(
        self,
        on_tab_created: Optional[Callable[[TabInfo], None]] = None,
        on_tab_closed: Optional[Callable[[str], None]] = None,
        on_tab_error: Optional[Callable[[str, Exception], None]] = None,
    ):
        """Set event callbacks for tab lifecycle events."""
        self._on_tab_created = on_tab_created
        self._on_tab_closed = on_tab_closed
        self._on_tab_error = on_tab_error
    
    def cleanup(self):
        """Clean up resources and close all tabs."""
        with self._tab_lock:
            for tab_id in list(self._tabs.keys()):
                self.close_tab(tab_id)
        
        self._executor.shutdown(wait=True)


# Global orchestrator instance per task_id
_orchestrators: Dict[str, TabOrchestrator] = {}
_orchestrator_lock = threading.Lock()


def get_orchestrator(
    task_id: str,
    max_tabs: int = 10,
    max_concurrent_ops: int = 5,
) -> TabOrchestrator:
    """
    Get or create a tab orchestrator for a task.
    
    Args:
        task_id: Task identifier
        max_tabs: Maximum number of tabs
        max_concurrent_ops: Maximum concurrent operations
    
    Returns:
        TabOrchestrator instance
    """
    with _orchestrator_lock:
        if task_id not in _orchestrators:
            _orchestrators[task_id] = TabOrchestrator(max_tabs, max_concurrent_ops)
        return _orchestrators[task_id]


def cleanup_orchestrator(task_id: str):
    """Clean up an orchestrator for a task."""
    with _orchestrator_lock:
        if task_id in _orchestrators:
            _orchestrators[task_id].cleanup()
            del _orchestrators[task_id]


def with_tab_orchestration(func):
    """
    Decorator to add tab orchestration to a browser function.
    
    Automatically manages tab lifecycle and provides tab context.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_id = kwargs.get('task_id')
        if not task_id:
            return func(*args, **kwargs)
        
        orchestrator = get_orchestrator(task_id)
        # Add orchestrator to kwargs
        kwargs['_orchestrator'] = orchestrator
        
        return func(*args, **kwargs)
    
    return wrapper
