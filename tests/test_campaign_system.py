"""A campaign that built its own system leaves none alive."""

import cod3s
import muscadet

from .models import series_declaration

RUN_PARAMS = {"nb_runs": 5, "schedule": [0.0, 5.0, 10.0], "seed": 4242}


def test_a_campaign_without_a_system_can_be_followed_by_another():
    """The caller never saw the system, so the caller cannot drop it."""
    document = series_declaration("CampaignTwice")
    for _ in range(2):
        muscadet.simulate_declaration_on("pycatshoo", document, RUN_PARAMS)


def test_delete():
    cod3s.terminate_session()
