import asyncio
from fastapi import Request, HTTPException
from main import InMemoryRateLimiter

def create_mock_request(client_ip: str, path: str = "/api/v1/test") -> Request:
    """Builds a mock ASGI Request with custom X-Forwarded-For header."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [
            (b"host", b"localhost:8000"),
            (b"x-forwarded-for", client_ip.encode("utf-8")),
            (b"content-type", b"application/json"),
        ],
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)

async def test_multi_ip_rate_limiting():
    print("=" * 60)
    print("   TESTING MULTI-IP RATE LIMITER & PROXY HEADER COUNTERS   ")
    print("=" * 60)

    # Allow 2 requests per 60 seconds
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60, action_name="unit test")

    ip_a = "198.51.100.14"
    ip_b = "203.0.113.88"

    print(f"\n[1] Sending requests from IP A ({ip_a})...")
    req_a1 = create_mock_request(ip_a)
    await limiter(req_a1)
    print(f"  Attempt 1: SUCCESS (Recorded counter: {len(limiter.requests[ip_a])})")

    req_a2 = create_mock_request(ip_a)
    await limiter(req_a2)
    print(f"  Attempt 2: SUCCESS (Recorded counter: {len(limiter.requests[ip_a])})")

    # 3rd request must trigger 429
    try:
        req_a3 = create_mock_request(ip_a)
        await limiter(req_a3)
        print("  [FAIL] Attempt 3 unexpectedly succeeded!")
        assert False, "IP A should have been rate limited on attempt 3"
    except HTTPException as e:
        print(f"  Attempt 3: RATE LIMITED as expected! (HTTP {e.status_code}: {e.detail})")
        assert e.status_code == 429

    print(f"\n[2] Probing IP B ({ip_b}) to verify independent counter isolation...")
    # IP B must succeed despite IP A being blocked
    req_b1 = create_mock_request(ip_b)
    await limiter(req_b1)
    print(f"  Attempt 1 for IP B: SUCCESS! (Independent counter: {len(limiter.requests[ip_b])})")
    assert len(limiter.requests[ip_b]) == 1

    req_b2 = create_mock_request(ip_b)
    await limiter(req_b2)
    print(f"  Attempt 2 for IP B: SUCCESS! (Independent counter: {len(limiter.requests[ip_b])})")
    assert len(limiter.requests[ip_b]) == 2

    # 3rd request for IP B must trigger 429
    try:
        req_b3 = create_mock_request(ip_b)
        await limiter(req_b3)
        print("  [FAIL] Attempt 3 for IP B unexpectedly succeeded!")
        assert False, "IP B should have been rate limited on attempt 3"
    except HTTPException as e:
        print(f"  Attempt 3 for IP B: RATE LIMITED as expected! (HTTP {e.status_code}: {e.detail})")
        assert e.status_code == 429

    # Re-verify IP A is STILL blocked
    try:
        await limiter(req_a3)
        assert False, "IP A should still be rate limited"
    except HTTPException as e:
        print(f"\n[3] Re-probe IP A ({ip_a}): STILL RATE LIMITED (HTTP {e.status_code})")

    # [4] Test Spoofed X-Forwarded-For protection
    print("\n[4] Testing Spoofed X-Forwarded-For protection...")
    real_proxy_client_ip = "192.0.2.100"
    limiter_spoof = InMemoryRateLimiter(max_requests=2, window_seconds=60, action_name="spoof test")

    # Attacker rotates fake IP on each request, but Render appends real client IP on the right
    req_spoof_1 = create_mock_request(f"1.1.1.1, {real_proxy_client_ip}")
    await limiter_spoof(req_spoof_1)
    print(f"  Attempt 1 (Client claims 1.1.1.1, Proxy appended {real_proxy_client_ip}): SUCCESS (Counter: {len(limiter_spoof.requests[real_proxy_client_ip])})")

    req_spoof_2 = create_mock_request(f"8.8.8.8, {real_proxy_client_ip}")
    await limiter_spoof(req_spoof_2)
    print(f"  Attempt 2 (Client claims 8.8.8.8, Proxy appended {real_proxy_client_ip}): SUCCESS (Counter: {len(limiter_spoof.requests[real_proxy_client_ip])})")

    try:
        req_spoof_3 = create_mock_request(f"44.55.66.77, {real_proxy_client_ip}")
        await limiter_spoof(req_spoof_3)
        assert False, "Attacker should have been blocked despite injecting fake IP 44.55.66.77"
    except HTTPException as e:
        print(f"  Attempt 3 (Client claims 44.55.66.77, Proxy appended {real_proxy_client_ip}): RATE LIMITED as expected! (HTTP {e.status_code})")
        assert e.status_code == 429
        print("  [OK] Proved: Injected fake client IPs share the same real counter and cannot bypass rate limiting.")

    print("\n" + "=" * 60)
    print("  [SUCCESS] All rate limiter & spoof protection checks passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_multi_ip_rate_limiting())
