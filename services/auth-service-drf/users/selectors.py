from .models import UserProfile


async def serialize_user(user):
    profile = user._state.fields_cache.get('profile')
    if profile is None:
        try:
            profile = await UserProfile.objects.aget(user=user)
        except UserProfile.DoesNotExist:
            profile = None

    return {
        'id': str(user.id),
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'last_login': user.last_login,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
        'profile': {
            'phone': profile.phone if profile else '',
            'avatar_url': profile.avatar_url if profile else '',
            'country': profile.country if profile else '',
            'currency_code': profile.currency_code if profile else '',
            'timezone': profile.timezone if profile else '',
            'date_of_birth': profile.date_of_birth if profile else None,
            'created_at': profile.created_at if profile else None,
            'updated_at': profile.updated_at if profile else None,
        },
    }


async def update_user_profile(user, profile_data):
    profile = user._state.fields_cache.get('profile')
    if profile is None:
        profile = await UserProfile.objects.acreate(user=user)
        user._state.fields_cache['profile'] = profile

    changed_fields = []
    for field, value in profile_data.items():
        setattr(profile, field, value)
        changed_fields.append(field)

    if changed_fields:
        changed_fields.append('updated_at')
        await profile.asave(update_fields=changed_fields)

    return profile
