import hashlib
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _


def hash_token(raw_token):
    if not raw_token:
        raise ValueError("Token value is required.")
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")
        if not username:
            raise ValueError("The username is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(
        _("password"), max_length=128, db_column="password_hash"
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"], name="users_email_idx"),
            models.Index(fields=["username"], name="users_username_idx"),
        ]

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=32, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    country = models.CharField(max_length=100, blank=True)
    currency_code = models.CharField(max_length=3, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile for {self.user.email}"


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    token_hash = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        db_table = "refresh_tokens"
        indexes = [
            models.Index(
                fields=["user", "is_revoked"], name="refresh_user_revoked_idx"
            ),
            models.Index(fields=["expires_at"], name="refresh_expires_idx"),
        ]

    def __str__(self):
        return f"Refresh token for {self.user.email}"

    @classmethod
    async def acreate_for_user(cls, user, raw_token, expires_at):
        return await cls.objects.acreate(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )

    @classmethod
    async def aget_valid(cls, raw_token):
        try:
            return await cls.objects.select_related("user").aget(
                token_hash=hash_token(raw_token),
                is_revoked=False,
                expires_at__gt=django_timezone.now(),
            )
        except cls.DoesNotExist:
            return None

    async def arevoke(self):
        self.is_revoked = True
        await self.asave(update_fields=["is_revoked"])


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token_hash = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(fields=["user", "is_used"], name="reset_user_used_idx"),
            models.Index(fields=["expires_at"], name="reset_expires_idx"),
        ]

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    @classmethod
    async def acreate_for_user(cls, user, raw_token, expires_at):
        return await cls.objects.acreate(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )

    @classmethod
    async def aget_valid(cls, raw_token):
        try:
            return await cls.objects.select_related("user").aget(
                token_hash=hash_token(raw_token),
                is_used=False,
                expires_at__gt=django_timezone.now(),
            )
        except cls.DoesNotExist:
            return None

    async def amark_used(self):
        self.is_used = True
        await self.asave(update_fields=["is_used"])


class ServiceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_tokens"
    )
    service_name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        db_table = "service_tokens"
        indexes = [
            models.Index(fields=["user", "service_name"], name="service_user_name_idx"),
            models.Index(
                fields=["is_active", "expires_at"], name="service_active_exp_idx"
            ),
        ]

    def __str__(self):
        return f"{self.service_name} token for {self.user.email}"

    @classmethod
    async def acreate_for_user(cls, user, service_name, raw_token, expires_at):
        return await cls.objects.acreate(
            user=user,
            service_name=service_name,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )

    @classmethod
    async def aget_active(cls, service_name, raw_token):
        try:
            return await cls.objects.select_related("user").aget(
                service_name=service_name,
                token_hash=hash_token(raw_token),
                is_active=True,
                expires_at__gt=django_timezone.now(),
            )
        except cls.DoesNotExist:
            return None

    async def adeactivate(self):
        self.is_active = False
        await self.asave(update_fields=["is_active"])
