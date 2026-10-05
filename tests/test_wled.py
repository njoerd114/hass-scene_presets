from scene_presets import wled


class Entry:
    def __init__(self, entity_id, device_id=None, domain="light", translation_key=None, unique_id=None):
        self.entity_id = entity_id
        self.device_id = device_id
        self.domain = domain
        self.translation_key = translation_key
        self.unique_id = unique_id


class Registry:
    def __init__(self, by_entity, entries):
        self.by_entity = by_entity
        self.entries = entries

    def async_get(self, entity_id):
        return self.by_entity.get(entity_id)


def entries_for_device(registry, device_id):
    return [entry for entry in registry.entries if entry.device_id == device_id]


def test_resolves_preset_select_on_the_same_device():
    light = Entry("light.wled", device_id="dev1")
    entries = [
        Entry("select.wled_preset", device_id="dev1", domain="select", translation_key="preset"),
        Entry("select.wled_playlist", device_id="dev1", domain="select", translation_key="playlist"),
        Entry("select.other_preset", device_id="dev2", domain="select", translation_key="preset"),
        Entry("light.wled_segment_1", device_id="dev1"),
    ]
    registry = Registry({"light.wled": light}, entries)

    result = wled.select_preset_entity_ids(registry, entries_for_device, ["light.wled"])

    assert result == ["select.wled_preset"]


def test_deduplicates_a_device_shared_by_several_segments():
    segments = [
        Entry("light.wled_segment_0", device_id="dev1"),
        Entry("light.wled_segment_1", device_id="dev1"),
    ]
    entries = [
        Entry("select.wled_preset", device_id="dev1", domain="select", translation_key="preset"),
    ]
    registry = Registry({entry.entity_id: entry for entry in segments}, entries)

    result = wled.select_preset_entity_ids(
        registry,
        entries_for_device,
        [entry.entity_id for entry in segments],
    )

    assert result == ["select.wled_preset"]


def test_light_without_device_is_skipped():
    registry = Registry({"light.orphan": Entry("light.orphan")}, [])

    assert wled.select_preset_entity_ids(registry, entries_for_device, ["light.orphan"]) == []


def test_unknown_light_is_skipped():
    registry = Registry({}, [])

    assert wled.select_preset_entity_ids(registry, entries_for_device, ["light.missing"]) == []


def test_resolves_palette_speed_and_intensity_for_a_segment():
    light = Entry("light.wled_segment_1", device_id="dev1", unique_id="aa:bb_1")
    siblings = [
        Entry("select.wled_palette", device_id="dev1", domain="select", unique_id="aa:bb_palette_1"),
        Entry("number.wled_speed", device_id="dev1", domain="number", unique_id="aa:bb_speed_1"),
        Entry("number.wled_intensity", device_id="dev1", domain="number", unique_id="aa:bb_intensity_1"),
        Entry("light.wled_segment_2", device_id="dev1", unique_id="aa:bb_2"),
    ]
    registry = Registry({"light.wled_segment_1": light}, siblings)

    result = wled.resolve_wled_controls(registry, entries_for_device, ["light.wled_segment_1"])

    assert result == [
        {
            "palette": "select.wled_palette",
            "speed": "number.wled_speed",
            "intensity": "number.wled_intensity",
        }
    ]


def test_main_light_without_segment_suffix_has_no_controls():
    main = Entry("light.wled", device_id="dev1", unique_id="aa:bb")
    registry = Registry({"light.wled": main}, [])

    assert wled.resolve_wled_controls(registry, entries_for_device, ["light.wled"]) == []


def test_main_light_falls_back_to_segment_zero_controls():
    main = Entry("light.wled", device_id="dev1", unique_id="aa:bb")
    siblings = [
        Entry("select.wled_palette", device_id="dev1", domain="select", unique_id="aa:bb_palette_0"),
        Entry("number.wled_speed", device_id="dev1", domain="number", unique_id="aa:bb_speed_0"),
        Entry("number.wled_intensity", device_id="dev1", domain="number", unique_id="aa:bb_intensity_0"),
    ]
    registry = Registry({"light.wled": main}, siblings)

    result = wled.resolve_wled_controls(registry, entries_for_device, ["light.wled"])

    assert result == [
        {
            "palette": "select.wled_palette",
            "speed": "number.wled_speed",
            "intensity": "number.wled_intensity",
        }
    ]


def test_segment_without_any_siblings_is_skipped():
    light = Entry("light.wled_segment_1", device_id="dev1", unique_id="aa:bb_1")
    registry = Registry({"light.wled_segment_1": light}, [light])

    assert wled.resolve_wled_controls(registry, entries_for_device, ["light.wled_segment_1"]) == []
