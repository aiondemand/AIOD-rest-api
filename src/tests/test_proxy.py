import pytest
from starlette.testclient import TestClient

from versioning import Version


@pytest.mark.parametrize("prefix", ["/aiod", "/test"])
def test_home_redirect_respects_proxy_header(prefix: str, client: TestClient):
    result = client.get("/", headers={"x-forwarded-prefix": prefix})
    assert f"{prefix}{client.version.prefix}/docs" in result.text  # type: ignore[attr-defined]


@pytest.mark.parametrize("prefix", ["/aiod", "/test"])
def test_oauth_redirect_respects_proxy_header(prefix: str, client: TestClient):
    result = client.get("/docs", headers={"x-forwarded-prefix": prefix})
    assert f"{prefix}{client.version.prefix}/docs/oauth2-redirect" in result.text  # type: ignore[attr-defined]
