import os
import django
from django.urls import resolve, Resolver404

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_url(path):
    print(f"Trying to resolve: {path}")
    try:
        match = resolve(path)
        print(f"✅ FOUND: {match.view_name} -> {match.func}")
    except Resolver404:
        print("❌ NOT FOUND")
    except Exception as e:
        print(f"⚠️ ERROR: {e}")

        print(f"⚠️ ERROR: {e}")

# [New] Print all URLs
def print_urls():
    from django.urls import get_resolver
    print("\n--- Available URLs ---")
    resolver = get_resolver()
    for pattern in resolver.url_patterns:
        print(pattern)
    print("----------------------\n")

if __name__ == "__main__":
    print_urls()
    check_url("/api/centers/verify-code/")
    check_url("/api/b2g_sync/connect/")
