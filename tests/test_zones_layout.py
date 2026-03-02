import json
from pathlib import Path


def test_zones_layout_schema_and_bounds():
    layout_path = Path("assets/zones_layout.json")
    assert layout_path.exists(), "assets/zones_layout.json is missing"

    data = json.loads(layout_path.read_text(encoding="utf-8-sig"))
    zones = data.get("zones", [])

    assert len(zones) == 15

    for zone in zones:
        assert "id" in zone
        assert "name" in zone
        polygons = zone.get("polygons", [])
        assert polygons, f"Zone {zone.get('id')} has no polygons"

        for polygon in polygons:
            assert len(polygon) >= 3
            for point in polygon:
                assert isinstance(point, list) and len(point) == 2
                x, y = point
                assert 0.0 <= float(x) <= 1.0
                assert 0.0 <= float(y) <= 1.0

        label = zone.get("label")
        assert isinstance(label, list) and len(label) == 2
        assert 0.0 <= float(label[0]) <= 1.0
        assert 0.0 <= float(label[1]) <= 1.0
