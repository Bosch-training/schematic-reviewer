"""Shared pytest fixtures (ST-04 sample dataset)."""

import pytest
from sample_dataset import SampleDataset, build_dataset


@pytest.fixture
def sample_dataset(tmp_path) -> SampleDataset:
    """Build the sanitized sample dataset in a temp directory."""
    return build_dataset(tmp_path)
