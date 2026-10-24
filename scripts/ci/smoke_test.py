"""Container integration checks using only the Python standard library.

No real Keycloak credentials or paid model calls. Database read routes prove
schema initialization and connectivity, but do not prove full banking workflows.
"""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def read(url, payload=None):
    request = Request(url)
    if payload is not None:
        request = Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
    with urlopen(request, timeout=5) as response:
        return response.read()


def wait_for(url):
    deadline = time.monotonic() + 180
    while True:
        try:
            result = json.loads(read(url))
            if result.get("status") == "ok":
                print(f"PASS health: {url}", flush=True)
                return
        except (OSError, URLError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Health endpoint did not become ready: {url}")
        time.sleep(3)


def main():
    # Test both direct services and Nginx proxy routes.
    for url in [
        "http://localhost:8000/health",
        "http://localhost:8090/health",
        "http://localhost:8001/health",
        "http://localhost:9001/health",
        "http://localhost:3000/user-api/health",
        "http://localhost:3000/transaction-api/health",
        "http://localhost:3000/activity-api/health",
        "http://localhost:3000/finance-agent-api/health",
    ]:
        wait_for(url)

    assert read("http://localhost:3000/frontend-health").strip() == b"healthy"
    html = read("http://localhost:3000/").decode().lower()
    assert '<div id="root"' in html, "Frontend did not serve the React entry page"
    print("PASS frontend page and health", flush=True)

    for path in ["/user-api/users", "/activity-api/activities/ci-smoke-user"]:
        rows = json.loads(read("http://localhost:3000" + path))
        assert isinstance(rows, list), f"Expected list from {path}"
        print(f"PASS database-backed read: {path}", flush=True)

    # FinanceAgent must reject unauthenticated requests before contacting the LLM.
    try:
        read("http://localhost:3000/finance-agent-api/chat", {"message": "Balance?"})
    except HTTPError as error:
        assert error.code == 401, f"Expected 401, received {error.code}"
    else:
        raise AssertionError("FinanceAgent accepted an unauthenticated chat request")
    print("PASS unauthenticated agent request rejected", flush=True)


if __name__ == "__main__":
    main()
