from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

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


class RegisterView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(RegisterSerializer, request.data)
        user = await register_user(data)
        if user is None:
            raise ValidationError({'detail': 'Email or username already exists.'})
        tokens = await issue_token_pair(user)

        return Response(
            {
                'user': await serialize_user(user),
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(LoginSerializer, request.data)
        user = await authenticate_user(data['email'], data['password'])
        tokens = await issue_token_pair(user)

        return Response(
            {
                'user': await serialize_user(user),
                'tokens': tokens,
            }
        )


class RefreshView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(RefreshSerializer, request.data)
        tokens = await rotate_refresh_token(data['refresh'])
        return Response({'tokens': tokens})


class MeView(AsyncAPIView):
    async def get(self, request):
        user = await get_authenticated_user(request)
        return Response({'user': await serialize_user(user)})

    async def patch(self, request):
        user = await get_authenticated_user(request)
        data = validate_serializer(UserUpdateSerializer, request.data)
        await update_user(user, data)

        if 'profile' in data:
            await update_user_profile(user, data['profile'])

        user = await User.objects.select_related('profile').aget(id=user.id)
        return Response({'user': await serialize_user(user)})


class LogoutView(AsyncAPIView):
    async def post(self, request):
        data = validate_serializer(LogoutSerializer, request.data)
        await revoke_refresh_token(data['refresh'])
        return Response(status=status.HTTP_204_NO_CONTENT)
