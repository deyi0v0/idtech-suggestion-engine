from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    GREETING = "greeting"
    ENVIRONMENT = "environment"
    TRANSACTION_PROFILE = "transaction_profile"
    TECHNICAL_CONTEXT = "technical_context"
    RECOMMENDATION = "recommendation"
    LEAD_CAPTURE = "lead_capture"
    COMPLETE = "complete"


class EnvironmentInfo(BaseModel):
    vertical: Optional[str] = None          # parking, transit, vending, retail, etc.
    indoor_outdoor: Optional[str] = None    # indoor, outdoor, outdoor harsh
    temperature_range: Optional[str] = None # e.g., "-20C to 65C"


class TransactionProfile(BaseModel):
    monthly_volume: Optional[int] = None
    average_ticket: Optional[float] = None


class TechnicalContext(BaseModel):
    power_source: Optional[str] = None           # wall outlet, USB, battery
    voltage: Optional[str] = None                # 12V, 24V, 5V
    card_types: Optional[List[str]] = None       # contact, contactless, magstripe
    needs_pin: Optional[bool] = None
    is_standalone: Optional[bool] = None
    host_interface: Optional[str] = None         # USB, RS232, Ethernet, etc.
    host_os: Optional[str] = None
    standalone_comms: Optional[str] = None       # Ethernet, WiFi, Cellular
    needs_display: Optional[bool] = None
    previous_products: Optional[List[str]] = None


class LeadInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None


class CollectedInfo(BaseModel):
    environment: EnvironmentInfo = Field(default_factory=EnvironmentInfo)
    transaction_profile: TransactionProfile = Field(default_factory=TransactionProfile)
    technical_context: TechnicalContext = Field(default_factory=TechnicalContext)
    lead: LeadInfo = Field(default_factory=LeadInfo)

    def merge(self, update: Dict[str, Any]) -> "CollectedInfo":
        """Merge a flat or nested dict into this CollectedInfo and return self."""
        for key, value in update.items():
            if key in ("environment", "transaction_profile", "technical_context", "lead"):
                sub = getattr(self, key)
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        if sub_val is not None:
                            setattr(sub, sub_key, sub_val)
                elif value is not None:
                    setattr(self, key, value)
            else:
                if value is not None:
                    setattr(self, key, value)
        return self

    def to_flat_constraints(self) -> Dict[str, Any]:
        """Convert collected info into the constraints dict used by product_filtering."""
        tc = self.technical_context
        env = self.environment

        constraints: Dict[str, Any] = {}

        if env.vertical:
            constraints["use_case"] = env.vertical
        if env.indoor_outdoor == "outdoor" or env.indoor_outdoor == "outdoor harsh":
            constraints["is_outdoor"] = True
        if env.temperature_range:
            # get a searchable temp string
            import re
            match = re.search(r'(-?\d+)', env.temperature_range)
            if match:
                constraints["operate_temperature"] = match.group(1)

        if tc.voltage:
            constraints["input_power"] = tc.voltage
        if tc.power_source:
            if "usb" in tc.power_source.lower():
                constraints["input_power"] = "USB"
            elif "wall" in tc.power_source.lower() or "outlet" in tc.power_source.lower():
                constraints["input_power"] = "VAC"
        if tc.host_interface:
            constraints["interface"] = tc.host_interface
        if tc.standalone_comms:
            constraints["interface"] = tc.standalone_comms
        if tc.is_standalone:
            constraints["is_standalone"] = True

        # Build extra_specs_filter from boolean/string needs
        extra_tags: List[str] = []
        if tc.needs_pin:
            extra_tags.append("PIN")
        if tc.needs_display:
            extra_tags.append("display")
        if env.indoor_outdoor and "outdoor" in env.indoor_outdoor:
            extra_tags.append("IP")
        if extra_tags:
            constraints["extra_specs_filter"] = ",".join(extra_tags)

        if tc.previous_products:
            constraints["search_query"] = tc.previous_products[0]

        if tc.card_types and "contactless" in tc.card_types:
            if "extra_specs_filter" in constraints:
                constraints["extra_specs_filter"] += ",contactless"
            else:
                constraints["extra_specs_filter"] = "contactless"

        return constraints

# Group the fields I should try to get by states
REQUIRED_FIELDS_BY_STATE = {
    ConversationState.GREETING: [
        "environment.vertical",
    ],
    ConversationState.ENVIRONMENT: [
        "environment.indoor_outdoor",
    ],
    ConversationState.TRANSACTION_PROFILE: [
        "transaction_profile.monthly_volume",
    ],
    ConversationState.TECHNICAL_CONTEXT: [
        "technical_context.card_types",
        "technical_context.needs_pin",
        "technical_context.is_standalone",
    ],
    ConversationState.LEAD_CAPTURE: [
        "lead.name",
        "lead.email",
    ],
    ConversationState.COMPLETE: [],
    ConversationState.RECOMMENDATION: [],
}

# Additional optional fields that trigger fast-forward the state machine if present
FAST_FORWARD_TRIGGERS = {
    ConversationState.GREETING: ["environment.indoor_outdoor"],
    ConversationState.ENVIRONMENT: ["technical_context.card_types", "technical_context.needs_pin"],
    ConversationState.TRANSACTION_PROFILE: ["technical_context.is_standalone", "technical_context.power_source"],
    ConversationState.TECHNICAL_CONTEXT: [],
}


def _field_is_set(collected: CollectedInfo, dotted_path: str) -> bool:
    """Check if a dotted path like 'environment.vertical' is set (non-None)."""
    parts = dotted_path.split(".")
    obj = collected
    for part in parts:
        val = getattr(obj, part, None)
        if val is None:
            return False
        obj = val
    return True


def state_order(state: ConversationState) -> int:
    """Return sortable index for a state (earlier = lower number)."""
    order = [
        ConversationState.GREETING,
        ConversationState.ENVIRONMENT,
        ConversationState.TRANSACTION_PROFILE,
        ConversationState.TECHNICAL_CONTEXT,
        ConversationState.RECOMMENDATION,
        ConversationState.LEAD_CAPTURE,
        ConversationState.COMPLETE,
    ]
    return order.index(state)


def determine_next_state(collected: CollectedInfo) -> ConversationState:
    """
    Pure function: given what we know, what state should the bot be in?
    Jumps forward if multiple fields are already filled.
    """

    # what's the first state with missing required fields?
    ordered = [
        ConversationState.GREETING,
        ConversationState.ENVIRONMENT,
        ConversationState.TRANSACTION_PROFILE,
        ConversationState.TECHNICAL_CONTEXT,
        ConversationState.RECOMMENDATION,
        ConversationState.LEAD_CAPTURE,
        ConversationState.COMPLETE,
    ]

    for state in ordered:
        required = REQUIRED_FIELDS_BY_STATE.get(state, [])
        all_set = all(_field_is_set(collected, path) for path in required)
        if not all_set:
            return state

    return ConversationState.COMPLETE


def should_fast_forward(collected: CollectedInfo, current_state: ConversationState) -> bool:
    """
    If user provided info beyond the current state, we can skip states ahead.
    Returns True if we should recompute the next state from scratch.
    """
    triggers = FAST_FORWARD_TRIGGERS.get(current_state, [])
    for path in triggers:
        if _field_is_set(collected, path):
            return True
    return False
