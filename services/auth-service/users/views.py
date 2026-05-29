from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.conf import settings

from .base_views import AsyncAPIView
from .models import User
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
    validate_serializer,
)
from .selectors import serialize_user, update_user_profile
from .services import (
    authenticate_user,
    get_authenticated_user,
    issue_token_pair,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
    update_user,
)

REFRESH_COOKIE_NAME = "polyglot_refresh"


def refresh_cookie_settings():
    return {
        "httponly": True,
        "secure": settings.REFRESH_COOKIE_SECURE,
        "samesite": "Lax",
        "path": "/",
        "max_age": int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    }


def response_with_refresh_cookie(payload, tokens, status_code=status.HTTP_200_OK):
    response = Response(payload, status=status_code)
    response.set_cookie(
        REFRESH_COOKIE_NAME, tokens["refresh"], **refresh_cookie_settings()
    )
    return response


def refresh_from_request(request, data):
    return data.get("refresh") or request.COOKIES.get(REFRESH_COOKIE_NAME)


class RegisterView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(RegisterSerializer, request.data)
        user = await register_user(data)
        if user is None:
            raise ValidationError({"detail": "Email or username already exists."})
        tokens = await issue_token_pair(user)

        return response_with_refresh_cookie(
            {
                "user": await serialize_user(user),
                "tokens": {"access": tokens["access"]},
            },
            tokens,
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(LoginSerializer, request.data)
        user = await authenticate_user(data["email"], data["password"])
        tokens = await issue_token_pair(user)

        return response_with_refresh_cookie(
            {
                "user": await serialize_user(user),
                "tokens": {"access": tokens["access"]},
            },
            tokens,
        )


class RefreshView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(RefreshSerializer, request.data)
        refresh = refresh_from_request(request, data)
        if not refresh:
            raise ValidationError({"detail": "Refresh token is required."})
        tokens = await rotate_refresh_token(refresh)
        return response_with_refresh_cookie(
            {"tokens": {"access": tokens["access"]}}, tokens
        )


class MeView(AsyncAPIView):
    async def get(self, request):
        user = await get_authenticated_user(request)
        return Response({"user": await serialize_user(user)})

    async def patch(self, request):
        user = await get_authenticated_user(request)
        data = validate_serializer(UserUpdateSerializer, request.data)
        await update_user(user, data)

        if "profile" in data:
            await update_user_profile(user, data["profile"])

        user = await User.objects.select_related("profile").aget(id=user.id)
        return Response({"user": await serialize_user(user)})


class LogoutView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(LogoutSerializer, request.data)
        refresh = refresh_from_request(request, data)
        if refresh:
            await revoke_refresh_token(refresh)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/", samesite="Lax")
        return response
