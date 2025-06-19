"""
Authentication middleware for Agno Sales Extension API

This module implements JWT-based authentication middleware for the FastAPI server.
Provides secure token validation and user authentication.
"""

import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    username: str
    email: str
    permissions: list[str]
    exp: datetime


class AuthManager:
    """Authentication manager for JWT tokens"""
    
    def __init__(self, secret_key: str = JWT_SECRET_KEY):
        """
        Initialize authentication manager.
        
        Args:
            secret_key: JWT secret key for token signing
        """
        self.secret_key = secret_key
        self.algorithm = JWT_ALGORITHM
        
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            user_data: User data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        try:
            to_encode = user_data.copy()
            
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
            
            to_encode.update({"exp": expire})
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            TokenData object with decoded token data
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            email: str = payload.get("email")
            permissions: list = payload.get("permissions", [])
            exp: datetime = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            
            if user_id is None or username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(
                user_id=user_id,
                username=username,
                email=email,
                permissions=permissions,
                exp=exp
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def check_permissions(self, token_data: TokenData, required_permissions: list[str]) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            token_data: Decoded token data
            required_permissions: List of required permissions
            
        Returns:
            True if user has all required permissions
        """
        user_permissions = set(token_data.permissions)
        required_permissions_set = set(required_permissions)
        
        return required_permissions_set.issubset(user_permissions)


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenData object with user information
    """
    token = credentials.credentials
    return auth_manager.verify_token(token)


async def require_permissions(required_permissions: list[str]):
    """
    Dependency factory to require specific permissions.
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        Dependency function
    """
    async def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not auth_manager.check_permissions(current_user, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return permission_checker


# Convenience functions for common permission checks
async def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin permissions"""
    if not auth_manager.check_permissions(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    return current_user


async def require_lead_access(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require lead access permissions"""
    if not auth_manager.check_permissions(current_user, ["lead_access"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lead access permissions required"
        )
    return current_user


async def require_message_send(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require message sending permissions"""
    if not auth_manager.check_permissions(current_user, ["message_send"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Message sending permissions required"
        )
    return current_user


# Development/testing authentication bypass
async def dev_auth_bypass() -> TokenData:
    """
    Development authentication bypass.
    Only use in development environment!
    """
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return TokenData(
        user_id="dev_user",
        username="developer",
        email="dev@example.com",
        permissions=["admin", "lead_access", "message_send"],
        exp=datetime.now(timezone.utc) + timedelta(hours=24)
    )


def create_dev_token() -> str:
    """
    Create a development token for testing.
    Only use in development environment!
    """
    if os.getenv("ENVIRONMENT") != "development":
        raise ValueError("Development tokens only available in development environment")
    
    user_data = {
        "user_id": "dev_user",
        "username": "developer", 
        "email": "dev@example.com",
        "permissions": ["admin", "lead_access", "message_send"]
    }
    
    return auth_manager.create_access_token(user_data)


# Example usage
if __name__ == "__main__":
    # Create a sample token for testing
    sample_user = {
        "user_id": "user123",
        "username": "john_doe",
        "email": "john@example.com",
        "permissions": ["lead_access", "message_send"]
    }
    
    token = auth_manager.create_access_token(sample_user)
    print(f"Sample token: {token}")
    
    # Verify the token
    decoded = auth_manager.verify_token(token)
    print(f"Decoded token: {decoded}")
