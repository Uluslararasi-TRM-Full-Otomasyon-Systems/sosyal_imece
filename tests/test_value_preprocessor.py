import pytest

from value_preprocessor import preprocess_metric_value


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (3, 30), (10, 100), (10.5, 10.5), (25, 25)],
)
def test_preprocess_metric_value(value, expected):
    assert preprocess_metric_value(value) == expected


@pytest.mark.parametrize("value", [True, "3", None])
def test_preprocess_metric_value_rejects_non_numeric_values(value):
    with pytest.raises(TypeError):
        preprocess_metric_value(value)


def test_monitoring_endpoint_preprocesses_cross_delay_and_errors():
    import monitoring_api

    response = monitoring_api.app.test_client().get("/metrics/realtime")

    assert response.status_code == 200
    assert response.get_json()["cross_delay"] == 25
    assert response.get_json()["errors"] == 10