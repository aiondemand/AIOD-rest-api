from connectors.example.enum import EnumConnectorStatus


def test_fetch_happy_path():
    connector = EnumConnectorStatus()
    resources = list(connector.fetch())
    assert set(resources) == {"published", "draft", "rejected"}
