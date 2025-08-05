"""
Database operations for MCP server tool usage logging.

This module provides a template for integrating SQLite database logging
into MCP servers with OAuth authentication.
"""

import os
import json
import logging
import aiosqlite
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    SQLite database manager for tool usage logging.
    
    This class provides a template for database integration in MCP servers,
    demonstrating patterns for:
    - Async SQLite operations
    - Schema management and migrations
    - User and tool usage tracking
    - Environment-based configuration
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses environment
                    variable DATABASE_PATH or defaults to 'mcp_server.db'
        """
        self.db_path = db_path or os.getenv("DATABASE_PATH", "mcp_server.db")
        self.enabled = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database logging {'enabled' if self.enabled else 'disabled'}")
        if self.enabled:
            logger.info(f"Database path: {self.db_path}")
    
    async def initialize(self) -> None:
        """Initialize database schema and create tables if they don't exist."""
        if not self.enabled:
            return
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Enable foreign key constraints
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Create users table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        first_seen DATETIME NOT NULL,
                        last_seen DATETIME NOT NULL
                    )
                """)
                
                # Create tool_usage_logs table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tool_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        user_email TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        arguments TEXT NOT NULL,
                        result TEXT,
                        timestamp DATETIME NOT NULL,
                        execution_time_ms INTEGER,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create indexes for better query performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tool_usage_user_id 
                    ON tool_usage_logs (user_id)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tool_usage_timestamp 
                    ON tool_usage_logs (timestamp)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tool_usage_tool_name 
                    ON tool_usage_logs (tool_name)
                """)
                
                await db.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def upsert_user(self, user_info: Dict[str, Any]) -> None:
        """
        Insert or update user information.
        
        Args:
            user_info: Dictionary containing user information from OAuth
        """
        if not self.enabled:
            return
            
        try:
            user_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "")
            
            if not user_id or not email:
                logger.warning("Missing required user information for database upsert")
                return
            
            now = datetime.now(timezone.utc)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user exists
                cursor = await db.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
                )
                exists = await cursor.fetchone()
                
                if exists:
                    # Update last_seen and name (in case it changed)
                    await db.execute("""
                        UPDATE users 
                        SET name = ?, last_seen = ?
                        WHERE user_id = ?
                    """, (name, now, user_id))
                else:
                    # Insert new user
                    await db.execute("""
                        INSERT INTO users (user_id, email, name, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, email, name, now, now))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to upsert user: {e}")
    
    async def log_tool_usage(
        self,
        user_info: Dict[str, Any],
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log tool usage to database.
        
        Args:
            user_info: User information from OAuth authentication
            tool_name: Name of the tool that was called
            arguments: Input arguments passed to the tool
            result: Output result from the tool (will be JSON serialized)
            execution_time_ms: Tool execution time in milliseconds
            success: Whether the tool execution was successful
            error_message: Error message if execution failed
        """
        if not self.enabled:
            return
            
        try:
            user_id = user_info.get("sub")
            user_email = user_info.get("email")
            
            if not user_id or not user_email:
                logger.warning("Missing user information for tool logging")
                return
            
            # Ensure user exists in database
            await self.upsert_user(user_info)
            
            # Serialize arguments and result to JSON
            arguments_json = json.dumps(arguments, default=str)
            result_json = json.dumps(result, default=str) if result is not None else None
            
            timestamp = datetime.now(timezone.utc)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO tool_usage_logs (
                        user_id, user_email, tool_name, arguments, result,
                        timestamp, execution_time_ms, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, user_email, tool_name, arguments_json, result_json,
                    timestamp, execution_time_ms, success, error_message
                ))
                
                await db.commit()
                
                logger.debug(f"Logged tool usage: {tool_name} by {user_email}")
                
        except Exception as e:
            logger.error(f"Failed to log tool usage: {e}")
    
    async def get_user_tool_usage(
        self,
        user_id: str,
        limit: int = 100,
        tool_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve tool usage logs for a specific user.
        
        Args:
            user_id: User ID to retrieve logs for
            limit: Maximum number of logs to retrieve
            tool_name: Optional filter by tool name
            
        Returns:
            List of tool usage log dictionaries
        """
        if not self.enabled:
            return []
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                if tool_name:
                    query = """
                        SELECT * FROM tool_usage_logs 
                        WHERE user_id = ? AND tool_name = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor = await db.execute(query, (user_id, tool_name, limit))
                else:
                    query = """
                        SELECT * FROM tool_usage_logs 
                        WHERE user_id = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor = await db.execute(query, (user_id, limit))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to retrieve user tool usage: {e}")
            return []
    
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get overall usage statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        if not self.enabled:
            return {"enabled": False}
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total users
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                total_users = (await cursor.fetchone())[0]
                
                # Get total tool calls
                cursor = await db.execute("SELECT COUNT(*) FROM tool_usage_logs")
                total_calls = (await cursor.fetchone())[0]
                
                # Get successful calls
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM tool_usage_logs WHERE success = 1"
                )
                successful_calls = (await cursor.fetchone())[0]
                
                # Get most used tools
                cursor = await db.execute("""
                    SELECT tool_name, COUNT(*) as count 
                    FROM tool_usage_logs 
                    GROUP BY tool_name 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                top_tools = await cursor.fetchall()
                
                return {
                    "enabled": True,
                    "total_users": total_users,
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
                    "top_tools": [{"name": row[0], "count": row[1]} for row in top_tools]
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve usage statistics: {e}")
            return {"enabled": True, "error": str(e)}

# Global database manager instance
db_manager = DatabaseManager()