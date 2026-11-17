import pytest

import main


@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    main.analysis_rate_limiter._requests.clear()
    main.analysis_rate_limiter.limit = 5
