from fastapi import Request, HTTPException, status, Depends

from config.dependencies import get_jwt_auth_manager
from exceptions import TokenExpiredError, InvalidTokenError
from security.interface import JWTAuthManagerInterface


def get_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header.

    :param request: FastAPI Request object.
    :return: Extracted token string.
    :raises HTTPException: If Authorization header is missing or invalid.
    """
    authorization: str = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )

    return token


def get_current_user(request: Request, jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager)):
    try:
        token = jwt_manager.decode_access_token(token=get_token(request))
        return token.get("user_id")
    except (TokenExpiredError,InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired.")
