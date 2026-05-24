from django.http import JsonResponse


def bad_request(request, exception):
    return JsonResponse({"detail": "Bad request."}, status=400)


def permission_denied(request, exception):
    return JsonResponse({"detail": "Permission denied."}, status=403)


def page_not_found(request, exception):
    return JsonResponse({"detail": "Not found."}, status=404)


def server_error(request):
    return JsonResponse({"detail": "Internal server error."}, status=500)
