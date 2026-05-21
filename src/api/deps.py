"""
Dependency Injection Module

Provides FastAPI dependencies for:
- Database sessions
- Authentication (JWT tokens)
- RBAC (Role-Based Access Control)
"""

import hashlib
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
if not REFRESH_SECRET_KEY:
    raise ValueError("JWT_REFRESH_SECRET_KEY environment variable is required")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


@dataclass
class User:
    """User model for dependency injection"""
    id: str
    username: str
    email: str
    role: str
    password_hash: str | None = None
    organization_id: str | None = None
    clearance_level: int = 1


@dataclass
class TokenData:
    """JWT token payload data"""
    sub: str
    email: str
    role: str
    exp: int
    iat: int
    type: str


ROLE_HIERARCHY = {
    "system_admin": 6,
    "content_admin": 5,
    "editor": 4,
    "reviewer": 3,
    "author": 2,
    "viewer": 1,
}

ROLE_PERMISSIONS = {
    "system_admin": {
        "*:*",
    },
    "content_admin": {
        "projects:*",
        "chapters:*",
        "terms:*",
        "knowledge_graph:*",
        "security:*",
        "monitor:*",
        "workflows:*",
        "users:read",
        "users:update",
    },
    "editor": {
        "projects:read",
        "chapters:*",
        "terms:*",
        "knowledge_graph:read",
        "knowledge_graph:create",
        "knowledge_graph:update",
        "knowledge_graph:delete",
        "security:scan",
        "security:doi_verify",
        "security:semantic_scan",
        "security:regulation_verify",
        "security:material_register",
        "security:material_verify",
        "security:concept_verify",
        "workflows:read",
    },
    "reviewer": {
        "projects:read",
        "chapters:read",
        "chapters:submit",
        "chapters:review",
        "terms:read",
        "knowledge_graph:read",
        "security:scan",
    },
    "author": {
        "projects:read",
        "chapters:create",
        "chapters:read",
        "chapters:submit",
        "chapters:update",
        "terms:read",
        "terms:create",
        "terms:update",
        "terms:lock",
        "terms:unlock",
        "terms:delete",
        "knowledge_graph:read",
        "knowledge_graph:create",
        "security:scan",
        "security:verify",
        "security:register",
        "workflows:read",
    },
    "viewer": {
        "projects:read",
        "chapters:read",
        "terms:read",
        "knowledge_graph:read",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    })
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> TokenData:
    """Decode and validate a JWT token"""
    try:
        secret = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")

        return TokenData(
            sub=payload.get("sub", ""),
            email=payload.get("email", ""),
            role=payload.get("role", "viewer"),
            exp=payload.get("exp", 0),
            iat=payload.get("iat", 0),
            type=payload.get("type", token_type),
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_INVALID",
                    "message": "Invalid or expired token",
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """Get current authenticated user from JWT token"""
    if not credentials:
        if hasattr(request.state, "user"):
            return request.state.user
        return None

    try:
        token_data = decode_token(credentials.credentials, "access")

        user = User(
            id=token_data.sub,
            username=token_data.sub,
            email=token_data.email,
            role=token_data.role,
        )

        request.state.user = user
        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_INVALID", "message": "Invalid authentication token"}},
            headers={"WWW-Authenticate": "Bearer"},
        )


class RBACChecker:
    """RBAC permission checker"""

    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        """Check if user has required permissions"""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
            )

        user_permissions = set(ROLE_PERMISSIONS.get(user.role, set()))

        if "*:*" in user_permissions:
            return user

        for required in self.required_permissions:
            resource, action = required.split(":")

            if f"{resource}:*" in user_permissions:
                continue

            if required not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "PERMISSION_DENIED",
                            "message": f"Permission denied. Required: {required}",
                        }
                    },
                )

        return user


def require_permission(*permissions: str):
    """Dependency factory for requiring specific permissions"""
    return RBACChecker(list(permissions))


def require_role(*roles: str):
    """Dependency factory for requiring specific roles"""

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
            )

        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ROLE_REQUIRED",
                        "message": f"Required role: {', '.join(roles)}",
                    }
                },
            )

        return user

    return dependency


def require_min_role(min_role: str):
    """Dependency factory for requiring minimum role level"""

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
            )

        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ROLE_LEVEL_TOO_LOW",
                        "message": f"Minimum required role: {min_role}",
                    }
                },
            )

        return user

    return dependency


async def get_current_active_user(
    user: User | None = Depends(get_current_user),
) -> User:
    """Get current active (authenticated) user"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
        )
    if user.role not in ROLE_HIERARCHY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_USER", "message": "User has invalid role"}},
        )
    return user


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """Get user if authenticated, None otherwise"""
    return await get_current_user(request, credentials)


class DatabaseSession:
    """Simple in-memory database session for development"""

    def __init__(self):
        self._users: dict = {}
        self._projects: dict = {}
        self._chapters: dict = {}
        self._terms: dict = {}
        self._concepts: dict = {}
        self._sessions: dict = {}
        self._sections: dict = {}

    def create_user(self, user_data: dict) -> User:
        user_id = generate_uuid()
        if "password" in user_data:
            from api.deps import get_password_hash
            password_hash = get_password_hash(user_data["password"])
        elif "password_hash" in user_data:
            password_hash = user_data["password_hash"]
        else:
            raise ValueError("Either 'password' or 'password_hash' must be provided")
        user = User(
            id=user_id,
            username=user_data["username"],
            email=user_data["email"],
            role=user_data.get("role", "viewer"),
            password_hash=password_hash,
            organization_id=user_data.get("organization_id"),
            clearance_level=user_data.get("clearance_level", 1),
        )
        self._users[user_id] = user
        return user

    def get_user_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def update_user(self, user_id: str, update_data: dict) -> User | None:
        if user_id in self._users:
            user = self._users[user_id]
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            return user
        return None

    def create_project(self, project_data: dict) -> dict:
        project_id = generate_uuid()
        project = {
            "id": project_id,
            "name": project_data["name"],
            "description": project_data.get("description"),
            "status": "draft",
            "owner_id": project_data.get("owner_id"),
            "total_chapters": project_data.get("total_chapters", 0),
            "current_progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._projects[project_id] = project
        return project

    def get_project(self, project_id: str) -> dict | None:
        return self._projects.get(project_id)

    def list_projects(self, owner_id: str = None) -> list[dict]:
        projects = list(self._projects.values())
        if owner_id:
            projects = [p for p in projects if p.get("owner_id") == owner_id]
        return projects

    def update_project(self, project_id: str, update_data: dict) -> dict | None:
        if project_id in self._projects:
            self._projects[project_id].update(update_data)
            self._projects[project_id]["updated_at"] = datetime.utcnow().isoformat()
            return self._projects[project_id]
        return None

    def delete_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    def create_chapter(self, chapter_data: dict) -> dict:
        chapter_id = generate_uuid()
        chapter = {
            "id": chapter_id,
            "project_id": chapter_data["project_id"],
            "title": chapter_data["title"],
            "order_num": chapter_data["order_num"],
            "status": "draft",
            "word_count": 0,
            "version": "1.0",
            "content_hash": None,
            "parent_chapter_id": chapter_data.get("parent_chapter_id"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._chapters[chapter_id] = chapter
        return chapter

    def get_chapter(self, chapter_id: str) -> dict | None:
        return self._chapters.get(chapter_id)

    def list_chapters_by_project(self, project_id: str) -> list[dict]:
        return [
            c for c in self._chapters.values()
            if c.get("project_id") == project_id
        ]

    def update_chapter(self, chapter_id: str, update_data: dict) -> dict | None:
        if chapter_id in self._chapters:
            self._chapters[chapter_id].update(update_data)
            self._chapters[chapter_id]["updated_at"] = datetime.utcnow().isoformat()
            return self._chapters[chapter_id]
        return None

    def delete_chapter(self, chapter_id: str) -> bool:
        if chapter_id in self._chapters:
            del self._chapters[chapter_id]
            return True
        return False

    def create_term(self, term_data: dict) -> dict:
        term_id = generate_uuid()
        term = {
            "id": term_id,
            "term": term_data["term"],
            "definition": term_data["definition"],
            "domain": term_data.get("domain"),
            "synonyms": term_data.get("synonyms", []),
            "locked": False,
            "version": 1,
            "first_defined_at": term_data.get("first_defined_at"),
            "usage_locations": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        self._terms[term_id] = term
        return term

    def get_term(self, term_id: str) -> dict | None:
        return self._terms.get(term_id)

    def list_terms(self, domain: str = None) -> list[dict]:
        terms = list(self._terms.values())
        if domain:
            terms = [t for t in terms if t.get("domain") == domain]
        return terms

    def update_term(self, term_id: str, update_data: dict) -> dict | None:
        if term_id in self._terms:
            self._terms[term_id].update(update_data)
            return self._terms[term_id]
        return None

    def delete_term(self, term_id: str) -> bool:
        if term_id in self._terms:
            del self._terms[term_id]
            return True
        return False

    def lock_term(self, term_id: str, reason: str = None) -> dict | None:
        if term_id in self._terms:
            self._terms[term_id]["locked"] = True
            self._terms[term_id]["lock_reason"] = reason
            return self._terms[term_id]
        return None

    def create_section(self, section_data: dict) -> dict:
        section_id = generate_uuid()
        section = {
            "id": section_id,
            "chapter_id": section_data["chapter_id"],
            "title": section_data["title"],
            "order_num": section_data["order_num"],
            "status": section_data.get("status", "draft"),
            "word_count": section_data.get("word_count", 0),
            "parent_section_id": section_data.get("parent_section_id"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._sections[section_id] = section
        return section

    def get_section(self, section_id: str) -> dict | None:
        return self._sections.get(section_id)

    def update_section(self, section_id: str, update_data: dict) -> dict | None:
        if section_id in self._sections:
            self._sections[section_id].update(update_data)
            self._sections[section_id]["updated_at"] = datetime.utcnow().isoformat()
            return self._sections[section_id]
        return None

    def delete_section(self, section_id: str) -> bool:
        if section_id in self._sections:
            del self._sections[section_id]
            return True
        return False

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    def add_session(self, user_id: str, token: str, expires_in: int = 1800) -> None:
        """Add a session with expiration time (default 30 minutes)."""
        expire_at = time.time() + expires_in
        self._sessions[token] = {"user_id": user_id, "expire_at": expire_at}

    def get_session(self, token: str) -> str | None:
        """Get session user_id if session exists and is not expired."""
        session = self._sessions.get(token)
        if not session:
            return None
        if time.time() > session.get("expire_at", 0):
            # Session expired, remove it
            del self._sessions[token]
            return None
        return session.get("user_id")


db_session = DatabaseSession()


async def get_db() -> DatabaseSession:
    """Get database session dependency"""
    return db_session
