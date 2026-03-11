from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.models.user import AuthenticatedUser
from app.services.auth_service import AuthService, auth_service
from app.services.document_service import DocumentService, document_service
from app.services.project_service import ProjectService, project_service


def get_auth_service() -> AuthService:
    return auth_service


def get_project_service() -> ProjectService:
    return project_service


def get_document_service() -> DocumentService:
    return document_service


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    service: Annotated[AuthService, Depends(get_auth_service)] = auth_service,
) -> AuthenticatedUser:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    return service.get_user_from_token(token)
