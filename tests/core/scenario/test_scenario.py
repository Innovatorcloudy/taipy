from datetime import timedelta

import pytest

from taipy.core.common.alias import ScenarioId
from taipy.core.cycle.cycle_manager import CycleManager
from taipy.core.data.in_memory import InMemoryDataNode
from taipy.core.data.scope import Scope
from taipy.core.exceptions.configuration import InvalidConfigurationId
from taipy.core.pipeline.pipeline import Pipeline
from taipy.core.pipeline.pipeline_manager import PipelineManager
from taipy.core.scenario.scenario import Scenario
from taipy.core.scenario.scenario_manager import ScenarioManager


def test_create_scenario(cycle, current_datetime):
    scenario_entity_1 = Scenario("foo", [], {"key": "value"}, is_master=True, cycle=cycle)
    assert scenario_entity_1.id is not None
    assert scenario_entity_1.config_id == "foo"
    assert scenario_entity_1.pipelines == {}
    assert scenario_entity_1.properties == {"key": "value"}
    assert scenario_entity_1.key == "value"
    assert scenario_entity_1.creation_date is not None
    assert scenario_entity_1.is_master
    assert scenario_entity_1.cycle == cycle
    assert scenario_entity_1.tags == set()

    scenario_entity_2 = Scenario("bar", [], {}, ScenarioId("baz"), creation_date=current_datetime)
    assert scenario_entity_2.id == "baz"
    assert scenario_entity_2.config_id == "bar"
    assert scenario_entity_2.pipelines == {}
    assert scenario_entity_2.properties == {}
    assert scenario_entity_2.creation_date == current_datetime
    assert not scenario_entity_2.is_master
    assert scenario_entity_2.cycle is None
    assert scenario_entity_2.tags == set()

    pipeline_entity = Pipeline("qux", {}, [])
    scenario_entity_3 = Scenario("quux", [pipeline_entity], {})
    assert scenario_entity_3.id is not None
    assert scenario_entity_3.config_id == "quux"
    assert len(scenario_entity_3.pipelines) == 1
    assert scenario_entity_3.qux == pipeline_entity
    assert scenario_entity_3.properties == {}
    assert scenario_entity_3.tags == set()

    pipeline_entity_1 = Pipeline("abcx", {}, [])
    scenario_entity_4 = Scenario("abcxy", [pipeline_entity_1], {})
    assert scenario_entity_4.id is not None
    assert scenario_entity_4.config_id == "abcxy"
    assert len(scenario_entity_4.pipelines) == 1
    assert scenario_entity_4.abcx == pipeline_entity_1
    assert scenario_entity_4.properties == {}
    assert scenario_entity_4.tags == set()

    with pytest.raises(InvalidConfigurationId):
        Scenario("foo bar", [], {})


def test_add_property_to_scenario():
    scenario = Scenario("foo", [], {"key": "value"})
    assert scenario.properties == {"key": "value"}
    assert scenario.key == "value"

    scenario.properties["new_key"] = "new_value"

    assert scenario.properties == {"key": "value", "new_key": "new_value"}
    assert scenario.key == "value"
    assert scenario.new_key == "new_value"


def test_add_cycle_to_scenario(cycle):
    scenario = Scenario("foo", [], {})
    assert scenario.cycle is None
    CycleManager._set(cycle)
    scenario.cycle = cycle

    assert scenario.cycle == cycle


def test_add_and_remove_subscriber():
    def mock_function():
        pass

    scenario = Scenario("foo", [], {})

    scenario.add_subscriber(mock_function)
    assert len(scenario.subscribers) == 1

    scenario.remove_subscriber(mock_function)
    assert len(scenario.subscribers) == 0


def test_add_and_remove_tag():
    scenario = Scenario("foo", [], {})

    assert len(scenario.tags) == 0
    scenario.add_tag("tag")
    assert len(scenario.tags) == 1

    scenario.remove_tag("tag")
    assert len(scenario.tags) == 0


def test_auto_set_and_reload(cycle, current_datetime, pipeline):
    scenario_1 = Scenario("foo", [], {}, creation_date=current_datetime, is_master=False, cycle=None)
    ScenarioManager._set(scenario_1)
    PipelineManager._set(pipeline)
    CycleManager._set(cycle)

    scenario_2 = ScenarioManager._get(scenario_1)
    assert scenario_1.config_id == "foo"
    scenario_1._config_id = "fgh"
    assert scenario_1.config_id == "foo"
    scenario_1.config_id = "fgh"
    assert scenario_1.config_id == "fgh"
    assert scenario_2.config_id == "fgh"

    assert len(scenario_1.pipelines) == 0
    scenario_1._pipelines = [pipeline]
    assert len(scenario_1.pipelines) == 0
    scenario_1.pipelines = [pipeline]
    assert len(scenario_1.pipelines) == 1
    assert scenario_1.pipelines[pipeline.config_id] == pipeline
    assert len(scenario_2.pipelines) == 1
    assert scenario_2.pipelines[pipeline.config_id] == pipeline

    new_datetime = current_datetime + timedelta(1)

    assert scenario_1.creation_date == current_datetime
    scenario_1._creation_date = new_datetime
    assert scenario_1.creation_date == current_datetime
    scenario_1.creation_date = new_datetime
    assert scenario_1.creation_date == new_datetime
    assert scenario_2.creation_date == new_datetime

    assert scenario_1.cycle is None
    scenario_1._cycle = cycle
    assert scenario_1.cycle is None
    scenario_1.cycle = cycle
    assert scenario_1.cycle == cycle
    assert scenario_2.cycle == cycle

    assert not scenario_1.is_master
    scenario_1._master_scenario = True
    assert not scenario_1.is_master
    scenario_1.is_master = True
    assert scenario_1.is_master
    assert scenario_2.is_master

    assert len(scenario_1.subscribers) == 0
    scenario_1._subscribers = set([print])
    assert len(scenario_1.subscribers) == 0
    scenario_1.subscribers = set([print])
    assert len(scenario_1.subscribers) == 1
    assert len(scenario_2.subscribers) == 1

    assert len(scenario_1.tags) == 0
    scenario_1._tags = set(["hi"])
    assert len(scenario_1.tags) == 0
    scenario_1.tags = set(["hi"])
    assert len(scenario_1.tags) == 1
    assert len(scenario_2.tags) == 1

    assert scenario_1.properties == {}
    scenario_1.properties["qux"] = 5
    assert scenario_1.properties["qux"] == 5
    assert scenario_2.properties["qux"] == 5

    with scenario_1 as scenario:
        assert scenario.config_id == "fgh"
        assert len(scenario.pipelines) == 1
        assert scenario.pipelines[pipeline.config_id] == pipeline
        assert scenario.creation_date == new_datetime
        assert scenario.cycle == cycle
        assert scenario.is_master
        assert len(scenario.subscribers) == 1
        assert len(scenario.tags) == 1
        assert scenario._is_in_context

        new_datetime_2 = new_datetime + timedelta(1)
        scenario.config_id = "abc"
        scenario.pipelines = []
        scenario.creation_date = new_datetime_2
        scenario.cycle = None
        scenario.is_master = False
        scenario.subscribers = None
        scenario.tags = None

        assert scenario._config_id == "abc"
        assert scenario.config_id == "fgh"
        assert len(scenario.pipelines) == 1
        assert scenario.pipelines[pipeline.config_id] == pipeline
        assert scenario.creation_date == new_datetime
        assert scenario.cycle == cycle
        assert scenario.is_master
        assert len(scenario.subscribers) == 1
        assert len(scenario.tags) == 1
        assert scenario._is_in_context

    assert scenario_1.config_id == "abc"
    assert len(scenario_1.pipelines) == 0
    assert scenario_1.creation_date == new_datetime_2
    assert scenario_1.cycle is None
    assert not scenario_1.is_master
    assert len(scenario_1.subscribers) == 0
    assert len(scenario_1.tags) == 0
    assert not scenario_1._is_in_context
