from scene_presets import dynamic_scenes as ds


class FakeScene:
    def __init__(self, scene_id, entity_ids):
        self.id = scene_id
        self.parameters = {"light_entity_ids": entity_ids}
        self.stopped = False

    def stop_loop(self):
        self.stopped = True

    def to_dict(self):
        return {"id": self.id}


def test_stop_all_stops_every_scene():
    manager = ds.DynamicSceneManager()
    first = FakeScene("a", ["light.x"])
    second = FakeScene("b", ["light.y"])
    manager.dynamic_scenes = {"a": first, "b": second}

    manager.stop_all()

    assert first.stopped and second.stopped
    assert manager.dynamic_scenes == {}


def test_stop_all_for_entity_only_stops_matching():
    manager = ds.DynamicSceneManager()
    matching = FakeScene("a", ["light.x"])
    other = FakeScene("b", ["light.y"])
    manager.dynamic_scenes = {"a": matching, "b": other}

    manager.stop_all_for_entity_id("light.x")

    assert matching.stopped
    assert not other.stopped
    assert set(manager.dynamic_scenes) == {"b"}


def test_delete_by_id_removes_and_stops():
    manager = ds.DynamicSceneManager()
    scene = FakeScene("a", [])
    manager.dynamic_scenes = {"a": scene}

    manager.delete_by_id("a")

    assert scene.stopped
    assert manager.dynamic_scenes == {}


def test_get_all_as_dict_serializes_scenes():
    manager = ds.DynamicSceneManager()
    manager.dynamic_scenes = {"a": FakeScene("a", [])}

    assert manager.get_all_as_dict() == {"dynamic_scenes": [{"id": "a"}]}
