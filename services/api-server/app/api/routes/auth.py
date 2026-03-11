from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.models.user import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return service.authenticate(payload.email, payload.password)
