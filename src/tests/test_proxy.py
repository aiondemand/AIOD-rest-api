import pytest
from starlette.testclient import TestClient

from versioning import Version


@pytest.mark.parametrize("prefix", ["/aiod", "/test"])
def test_home_redirect_respects_proxy_header(prefix: str, client: TestClient):
    result = client.get("/", headers={"x-forwarded-prefix": prefix})
    version_prefix = "" if client.version == Version.LATEST else f"/{client.version}"  # type: ignore[attr-defined]
    assert f"{prefix}{version_prefix}/docs" in result.text


@pytest.mark.parametrize("prefix", ["/aiod", "/test"])
def test_oauth_redirect_respects_proxy_header(prefix: str, client: TestClient):
    result = client.get("/docs", headers={"x-forwarded-prefix": prefix})
    version_prefix = "" if client.version == Version.LATEST else f"/{client.version}"  # type: ignore[attr-defined]
    assert f"{prefix}{version_prefix}/docs/oauth2-redirect" in result.text
