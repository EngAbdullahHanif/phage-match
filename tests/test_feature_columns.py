import pytest

from scripts.validate_feature_columns import validate_columns


def test_rejects_assay_and_unregistered_columns():
    manifest = {"version": 1, "columns": {
        "toy_value": {"role": "host", "source": "synthetic fixture", "dtype": "float64"},
    }}
    validate_columns(["host_id", "toy_value"], manifest)
    for name in ("category", "binary", "virulence_index", "inhibition_efficiency"):
        with pytest.raises(ValueError, match=f"blocked: {name}"):
            validate_columns(["host_id", "toy_value", name], manifest)
    with pytest.raises(ValueError, match="Unregistered feature columns: other"):
        validate_columns(["other"], manifest)
