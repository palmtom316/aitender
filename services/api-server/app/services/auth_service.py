from fastapi import HTTPException, status

from app.models.user import AuthenticatedUser, LoginResponse, User, UserRole


class AuthService:
    def __init__(self) -> None:
        self._users = {
            "admin@aitender.local": User(
                id="user-admin",
                organization_id="org-1",
                email="admin@aitender.local",
                password="admin-pass",
                role=UserRole.ADMIN,
                display_name="Admin User",
            ),
            "pm@aitender.local": User(
                id="user-pm",
                organization_id="org-1",
                email="pm@aitender.local",
                password="pm-pass",
                role=UserRole.PROJECT_MANAGER,
                display_name="Project Manager",
            ),
            "writer@aitender.local": User(
                id="user-writer",
                organization_id="org-1",
                email="writer@aitender.local",
                password="writer-pass",
                role=UserRole.WRITER,
                display_name="Bid Writer",
            ),
            "viewer@aitender.local": User(
                id="user-viewer",
                organization_id="org-1",
                email="viewer@aitender.local",
                password="viewer-pass",
                role=UserRole.VIEWER,
                display_name="Read Only Viewer",
            ),
        }
        self._tokens_by_user_id = {
            "user-admin": "auth-token-admin",
            "user-pm": "auth-token-pm",
            "user-writer": "auth-token-writer",
            "user-viewer": "auth-token-viewer",
        }

    def authenticate(self, email: str, password: str) -> LoginResponse:
        user = self._users.get(email)
        if user is None or user.password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        return LoginResponse(
            access_token=self._token_for_user(user),
            user=self._as_authenticated_user(user),
        )

    def get_user_from_token(self, token: str) -> AuthenticatedUser:
        for user in self._users.values():
            if self._token_for_user(user) == token:
                return self._as_authenticated_user(user)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )

    @staticmethod
    def _as_authenticated_user(user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.id,
            organization_id=user.organization_id,
            role=user.role,
            display_name=user.display_name,
        )

    def _token_for_user(self, user: User) -> str:
        return self._tokens_by_user_id[user.id]


auth_service = AuthService()
