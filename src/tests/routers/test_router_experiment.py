import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    body = copy.copy(body_asset)
    body["pid"] = "https://doi.org/10.1000/182"
    body["experimental_workflow"] = "Example workflow."
    body["execution_settings"] = "Example execution settings."
    body["reproducibility_explanation"] = "Example reproducibility explanation."

    distribution = {
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "checksum_algorithm": "sha256",
        "copyright": "2010-2020 Example Company. All rights reserved.",
        "content_url": "https://www.example.com/resource.pdf",
        "content_size_kb": 42,
        "date_published": "2022-01-01T15:15:00",
        "description": "A downloadable instance of this resource",
        "encoding_format": "application/pdf",
        "name": "resource.pdf",
        "installation_script": "./install.sh",
        "installation": "Build the Dockerfile",
        "installation_time_milliseconds": 100,
        "deployment_script": "./run.sh",
        "deployment": "You can run the run.py file using python3. See README.md for required "
        "arguments.",
        "deployment_time_milliseconds": 100,
        "os_requirement": "Windows 11.",
        "dependency": "Python packages as listed in requirements.txt.",
        "hardware_requirement": "4GB RAM; 100MB storage; 1GHz processor with 8 cores.",
    }
    body["distribution"] = [distribution]

    response = client.post("/experiments/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/experiments/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["pid"] == "https://doi.org/10.1000/182"
    assert response_json["experimental_workflow"] == "Example workflow."
    assert response_json["execution_settings"] == "Example execution settings."
    assert response_json["reproducibility_explanation"] == "Example reproducibility explanation."
    assert response_json["distribution"] == [distribution]
