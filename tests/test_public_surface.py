from importlib.util import find_spec

import polygres
from polygres import Polygres


def test_embedding_configuration_is_not_a_public_sdk_surface() -> None:
    with Polygres(
        api_key="poly_live_0123456789abcdef0123456789abcdef",
        runtime_url="https://runtime.example.test/v1",
    ) as client:
        assert not hasattr(client.project(), "embeddings")
    assert find_spec("polygres.embeddings") is None
    assert find_spec("polygres.embedding_models") is None
    assert not hasattr(polygres, "EmbeddingConfigurationCreate")
