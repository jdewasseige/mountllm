"""Basic tests for MountLLM project."""

from pathlib import Path

import pytest

from src.api.camptocamp import CamptocampClient
from src.api.models import CamptocampItem, Hut, Route, Summit
from src.data.collector import DataCollector


def test_imports():
    """Test that all modules can be imported."""
    assert True


def test_route_model():
    """Test Route model creation."""
    route_data = {
        "id": 12345,
        "title": "Test Route",
        "summary": "A test climbing route",
        "license": "CC-BY-SA",
    }

    route = Route(**route_data)
    assert route.id == 12345
    assert route.title == "Test Route"
    assert route.summary == "A test climbing route"
    assert route.license == "CC-BY-SA"


def test_summit_model():
    """Test Summit model creation."""
    summit_data = {
        "id": 67890,
        "title": "Test Summit",
        "elevation": 3000,
        "license": "CC-BY-SA",
    }

    summit = Summit(**summit_data)
    assert summit.id == 67890
    assert summit.title == "Test Summit"
    assert summit.elevation == 3000
    assert summit.license == "CC-BY-SA"


def test_hut_model():
    """Test Hut model creation."""
    hut_data = {
        "id": 11111,
        "title": "Test Hut",
        "elevation": 2500,
        "capacity": 20,
        "license": "CC-BY-SA",
    }

    hut = Hut(**hut_data)
    assert hut.id == 11111
    assert hut.title == "Test Hut"
    assert hut.elevation == 2500
    assert hut.capacity == 20
    assert hut.license == "CC-BY-SA"


def test_camptocamp_item():
    """Test CamptocampItem creation."""
    route = Route(id=12345, title="Test Route", license="CC-BY-SA")

    item = CamptocampItem(
        item_type="routes",
        data=route,
        raw_response={"id": 12345, "title": "Test Route"},
    )

    assert item.item_type == "routes"
    assert item.data.id == 12345
    assert item.data.title == "Test Route"


def test_data_collector_creation():
    """Test DataCollector instantiation."""
    collector = DataCollector(
        output_dir="./test_data", max_items_per_category=100, rate_limit=50
    )

    assert collector.output_dir == Path("./test_data")
    assert collector.max_items_per_category == 100
    assert collector.rate_limit == 50


def test_project_structure():
    """Test that project structure is correct."""
    project_root = Path(__file__).parent.parent

    # Check main directories exist
    assert (project_root / "src").exists()
    assert (project_root / "src" / "api").exists()
    assert (project_root / "src" / "data").exists()
    assert (project_root / "src" / "utils").exists()
    assert (project_root / "data").exists()

    # Check main files exist
    assert (project_root / "main.py").exists()
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "README.md").exists()


if __name__ == "__main__":
    pytest.main([__file__])
