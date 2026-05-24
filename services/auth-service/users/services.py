from datetime import datetime, timezone

from django.db import IntegrityError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken as JWTRefreshToken

from .models import RefreshToken, User, UserProfile


def token_expiry(token):
    return datetime.fromtimestamp(token["exp"], tz=timezone.utc)


async def issue_token_pair(user):
    refresh = JWTRefreshToken.for_user(user)
    access = refresh.access_token
    await RefreshToken.acreate_for_user(user, str(refresh), token_expiry(refresh))
    return {
        "access": str(access),
        "refresh": str(refresh),
    }


async def register_user(data):
    user = User(
        email=User.objects.normalize_email(data["email"]),
        username=data["username"],
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
    )
    user.set_password(data["password"])

    try:
        await user.asave()
        profile = await UserProfile.objects.acreate(user=user)
        user._state.fields_cache["profile"] = profile
    except IntegrityError:
        return None

    return user


async def authenticate_user(email, password):
    try:
        user = await User.objects.select_related("profile").aget(
            email__iexact=email, is_active=True
        )
    except User.DoesNotExist as exc:
        raise AuthenticationFailed("Invalid email or password.") from exc

    if not await user.acheck_password(password):
        raise AuthenticationFailed("Invalid email or password.")

    return user


async def get_authenticated_user(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationFailed("Bearer access token is required.")

    raw_token = auth_header.removeprefix("Bearer ").strip()
    try:
        token = AccessToken(raw_token)
        user_id = token["user_id"]
    except TokenError as exc:
        raise AuthenticationFailed("Invalid or expired access token.") from exc

    try:
        return await User.objects.select_related("profile").aget(
            id=user_id, is_active=True
        )
    except User.DoesNotExist as exc:
        raise AuthenticationFailed("User not found or inactive.") from exc


async def rotate_refresh_token(raw_refresh):
    stored_token = await RefreshToken.aget_valid(raw_refresh)
    if stored_token is None:
        raise AuthenticationFailed("Invalid, expired, or revoked refresh token.")

    try:
        incoming_refresh = JWTRefreshToken(raw_refresh)
        user_id = incoming_refresh["user_id"]
    except TokenError as exc:
        raise AuthenticationFailed("Invalid or expired refresh token.") from exc

    if str(stored_token.user_id) != str(user_id):
        raise AuthenticationFailed("Refresh token user mismatch.")

    await stored_token.arevoke()
    return await issue_token_pair(stored_token.user)


async def revoke_refresh_token(raw_refresh):
    stored_token = await RefreshToken.aget_valid(raw_refresh)
    if stored_token is not None:
        await stored_token.arevoke()


async def update_user(user, data):
    changed_fields = []
    for field in ("first_name", "last_name"):
        if field in data:
            setattr(user, field, data[field])
            changed_fields.append(field)

    if changed_fields:
        changed_fields.append("updated_at")
        await user.asave(update_fields=changed_fields)

    return user
