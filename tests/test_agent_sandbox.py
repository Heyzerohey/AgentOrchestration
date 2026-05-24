import pytest
from src.agent.sandbox import ResourceLimits, AgentSandbox
from src.common.config import Config


class TestResourceLimitsValidation:
    def test_valid_limits(self):
        limits = ResourceLimits(cpu_time=30, memory_mb=256, disk_mb=50)
        assert limits.cpu_time == 30
        assert limits.memory_mb == 256
        assert limits.disk_mb == 50

    def test_default_limits(self):
        limits = ResourceLimits()
        assert limits.cpu_time == 60
        assert limits.memory_mb == 512
        assert limits.disk_mb == 100

    def test_negative_limits_raise_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            ResourceLimits(cpu_time=-10)

        with pytest.raises(ValueError, match="must be positive"):
            ResourceLimits(memory_mb=0)

        with pytest.raises(ValueError, match="must be positive"):
            ResourceLimits(disk_mb=-5)

    def test_non_numeric_limits_raise_type_error(self):
        with pytest.raises(TypeError, match="must be numeric"):
            ResourceLimits(cpu_time="30")

        with pytest.raises(TypeError, match="must be numeric"):
            ResourceLimits(memory_mb=[512])

        with pytest.raises(TypeError, match="must be numeric"):
            ResourceLimits(disk_mb={"disk": 100})


class TestConfigResourceLimitsValidation:
    def test_valid_config(self):
        config = Config()
        config.set("sandbox.cpu_time", 45)
        config.set("sandbox.memory_mb", 1024)
        config.set("sandbox.disk_mb", 200)

        # Should not raise any exception
        config.validate_resource_limits()

    def test_negative_config_raises_value_error(self):
        config = Config()
        config.set("sandbox.cpu_time", -10)
        with pytest.raises(ValueError, match="must be positive"):
            config.validate_resource_limits()

        config = Config()
        config.set("sandbox.memory_mb", 0)
        with pytest.raises(ValueError, match="must be positive"):
            config.validate_resource_limits()

    def test_non_numeric_config_raises_type_error(self):
        config = Config()
        config.set("sandbox.cpu_time", "60")
        with pytest.raises(TypeError, match="must be numeric"):
            config.validate_resource_limits()

        config = Config()
        config.set("sandbox.memory_mb", True) # True is numeric/boolean, but let's check
        # Wait, isinstance(True, int) is True, so standard checks might not catch it,
        # but let's test a string or list
        config.set("sandbox.disk_mb", [100])
        with pytest.raises(TypeError, match="must be numeric"):
            config.validate_resource_limits()
