"""Subpackage with the orchestrating agents used by the dynamic ADK pipeline."""
from .roach_motel_agent import roach_motel_root_agent
from .fake_urgency_agent import fake_urgency_root_agent
from .fake_scarcity_agent import fake_scarcity_root_agent
from .drip_pricing_agent import drip_pricing_root_agent
from .hidden_subscription_agent import hidden_subscription_root_agent
from .sneak_into_basket_agent import sneak_into_basket_root_agent
from .bait_and_switch_agent import bait_and_switch_root_agent
from .confirmshaming_agent import confirmshaming_root_agent
from .forced_actions_agent import forced_actions_root_agent
from .nagging_agent import nagging_root_agent
from .navigation_obstacles_agent import navigation_obstacles_root_agent
from .currency_manipulation_agent import currency_manipulation_root_agent
from .browser_agent import ingest_agent, browser_loop
__all__ = [
    "pipeline",
    "browser_agent",
    'roach_motel_root_agent',
    'fake_urgency_root_agent',
    'fake_scarcity_root_agent',
    'drip_pricing_root_agent',
    'hidden_subscription_root_agent',
    'sneak_into_basket_root_agent',
    'bait_and_switch_root_agent',
    'confirmshaming_root_agent',
    'forced_actions_root_agent',
    'nagging_root_agent',
    'navigation_obstacles_root_agent',
    'currency_manipulation_root_agent',
    'ingest_agent',
    'browser_loop'
]
