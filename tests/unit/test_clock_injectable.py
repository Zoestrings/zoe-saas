from datetime import datetime, timezone, timedelta
import pytest
from zoe.clock.clock import FakeClock, set_clock, get_clock, now, Clock


@pytest.mark.automated
def test_clock_injectable() -> None:
    fixed_time = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    fake = FakeClock(fixed_time)
    set_clock(fake)

    try:
        assert now() == fixed_time
        fake.advance(seconds=5)
        expected_advanced = fixed_time + timedelta(seconds=5)
        assert now() == expected_advanced
    finally:
        # Restore default clock
        set_clock(Clock())

