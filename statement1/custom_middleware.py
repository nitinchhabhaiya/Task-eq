import datetime
from django.core.cache import cache
from django.http import JsonResponse
from .models import BlockedIPAddress

class IPLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = self.get_client_ip(request)

        # Check if the IP address is blocked permanently
        if BlockedIPAddress.objects.filter(ip_address=ip_address).exists():
            return JsonResponse({'message': 'IP is blocked permanently.'}, status=403)

        # Check if the IP address is blocked temporarily
        if cache.get(f'blocked_ip:{ip_address}'):
            return JsonResponse({'message': 'IP is blocked temporarily. Try again later.'}, status=429)

        # Increment request count for the IP address
        request_count = cache.get(f'request_count:{ip_address}', 0)
        request_count += 1
        print(request_count)
        cache.set(f'request_count:{ip_address}', request_count, 60)  # Store for 1 minute

        # Check rate limit
        if request_count > 100:
            BlockedIPAddress.objects.create(ip_address=ip_address, request_count=request_count)
            return JsonResponse({'message': 'IP is blocked permanently.'}, status=403)

        # Check if the rate limit is exceeded
        if request_count > 10:
            cache.set(f'blocked_ip:{ip_address}', 'blocked', 1200)  # Block for 20 minutes
            return JsonResponse({'message': 'IP is blocked temporarily. Try again later.'}, status=429)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
