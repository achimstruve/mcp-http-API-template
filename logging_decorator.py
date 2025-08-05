"""
Tool logging decorator for MCP servers.

This module provides a decorator to automatically log tool usage
with OAuth user context to a SQLite database. This serves as a
template for integrating database logging into MCP servers.
"""

import time
import logging
import asyncio
import functools
from typing import Any, Callable, Dict, Optional, Union
from inspect import iscoroutinefunction

from database import db_manager

logger = logging.getLogger(__name__)

def logged_tool(func: Callable) -> Callable:
    """
    Decorator to automatically log MCP tool usage.
    
    This decorator captures:
    - Tool name and arguments
    - Execution time and success status
    - User information from request context
    - Results and error messages
    
    The decorator works with both sync and async functions and
    integrates with the existing OAuth authentication system.
    
    Args:
        func: The MCP tool function to wrap
        
    Returns:
        Wrapped function with automatic logging
    """
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        # Get tool name from function
        tool_name = getattr(func, '__name__', 'unknown_tool')
        
        # Combine positional and keyword arguments
        all_args = {}
        
        # Handle positional arguments
        if hasattr(func, '__code__'):
            param_names = func.__code__.co_varnames[:func.__code__.co_argcount]
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_args[param_names[i]] = arg
        
        # Add keyword arguments
        all_args.update(kwargs)
        
        # Try to get user context from various sources
        user_info = await _get_user_context()
        
        # Start timing
        start_time = time.time()
        success = True
        result = None
        error_message = None
        
        try:
            # Call the original function
            if iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Tool {tool_name} failed: {error_message}")
            raise
            
        finally:
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log to database if we have user info
            if user_info:
                try:
                    await db_manager.log_tool_usage(
                        user_info=user_info,
                        tool_name=tool_name,
                        arguments=all_args,
                        result=result,
                        execution_time_ms=execution_time_ms,
                        success=success,
                        error_message=error_message
                    )
                except Exception as log_error:
                    logger.error(f"Failed to log tool usage: {log_error}")
            else:
                logger.debug(f"No user context available for tool {tool_name}")
        
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        # For sync functions, we need to handle the async logging differently
        # This wrapper converts sync tools to work with async logging
        
        # Get tool name from function
        tool_name = getattr(func, '__name__', 'unknown_tool')
        
        # Combine positional and keyword arguments
        all_args = {}
        
        # Handle positional arguments
        if hasattr(func, '__code__'):
            param_names = func.__code__.co_varnames[:func.__code__.co_argcount]
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_args[param_names[i]] = arg
        
        # Add keyword arguments
        all_args.update(kwargs)
        
        # Start timing
        start_time = time.time()
        success = True
        result = None
        error_message = None
        
        try:
            # Call the original function
            result = func(*args, **kwargs)
            
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Tool {tool_name} failed: {error_message}")
            raise
            
        finally:
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Schedule async logging - this will be handled by the event loop
            asyncio.create_task(_log_sync_tool_usage(
                tool_name=tool_name,
                arguments=all_args,
                result=result,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message
            ))
        
        return result
    
    # Return appropriate wrapper based on function type
    if iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

async def _get_user_context() -> Optional[Dict[str, Any]]:
    """
    Extract user context from the current request.
    
    This function attempts to retrieve user information from various
    sources that might be available in the MCP server context.
    
    Returns:
        User information dictionary if available, None otherwise
    """
    # In a real implementation, this would extract user info from:
    # 1. Request context/scope (if available)
    # 2. Thread-local storage
    # 3. Context variables
    # 4. Other application-specific mechanisms
    
    # For this template, we'll try to get it from a context variable
    # that should be set by the OAuth middleware
    try:
        import contextvars
        
        # Try to get user context from context variable
        # This would need to be set by the OAuth middleware
        user_context_var = contextvars.ContextVar('user_context', default=None)
        user_info = user_context_var.get()
        
        if user_info:
            return user_info
            
    except Exception as e:
        logger.debug(f"Could not retrieve user context from context variables: {e}")
    
    # Fallback: try to get from current task context if available
    try:
        current_task = asyncio.current_task()
        if current_task and hasattr(current_task, 'user_info'):
            return getattr(current_task, 'user_info')
    except Exception as e:
        logger.debug(f"Could not retrieve user context from task: {e}")
    
    # No user context available
    return None

async def _log_sync_tool_usage(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any = None,
    execution_time_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """
    Async helper function to log sync tool usage.
    
    This function is called from the sync wrapper to handle
    async database logging for synchronous tools.
    """
    try:
        user_info = await _get_user_context()
        
        if user_info:
            await db_manager.log_tool_usage(
                user_info=user_info,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message
            )
        else:
            logger.debug(f"No user context available for sync tool {tool_name}")
            
    except Exception as e:
        logger.error(f"Failed to log sync tool usage: {e}")

def set_user_context(user_info: Dict[str, Any]) -> None:
    """
    Set user context for the current request.
    
    This should be called by the OAuth middleware to make
    user information available to the logging decorator.
    
    Args:
        user_info: User information from OAuth authentication
    """
    try:
        import contextvars
        
        user_context_var = contextvars.ContextVar('user_context', default=None)
        user_context_var.set(user_info)
        
        # Also set on current task if available
        try:
            current_task = asyncio.current_task()
            if current_task:
                setattr(current_task, 'user_info', user_info)
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Failed to set user context: {e}")

def clear_user_context() -> None:
    """
    Clear user context for the current request.
    
    This should be called at the end of request processing
    to clean up context variables.
    """
    try:
        import contextvars
        
        user_context_var = contextvars.ContextVar('user_context', default=None)
        user_context_var.set(None)
        
        # Also clear from current task if available
        try:
            current_task = asyncio.current_task()
            if current_task and hasattr(current_task, 'user_info'):
                delattr(current_task, 'user_info')
        except Exception:
            pass
            
    except Exception as e:
        logger.debug(f"Failed to clear user context: {e}")