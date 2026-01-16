"""Workflow state models and dependency container."""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class WorkflowStep(str, Enum):
    """Flight rescheduling workflow steps."""

    IDLE = "idle"
    FLIGHT_SELECTION = "flight_selection"
    SEAT_SELECTION = "seat_selection"
    PAYMENT = "payment"
    COMPLETED = "completed"


class FlightInfo(BaseModel):
    """Flight information model."""

    flight_id: str
    flight_number: str
    departure: str  # Airport code (e.g., "IST")
    arrival: str  # Airport code (e.g., "AYT")
    departure_time: str  # Time string (e.g., "14:00")
    fare_class: str  # Fare class code (e.g., "W", "P")
    fare_difference: float = 0.0  # Difference from original fare in TRY


class SeatOption(BaseModel):
    """Seat selection option."""

    seat_id: str
    seat_number: str  # e.g., "12A"
    seat_type: str  # "window", "aisle", "middle"
    price: float  # Price in TRY
    row_type: str  # "standard", "extra_legroom", "emergency"


class ReschedulingState(BaseModel):
    """Complete state for flight rescheduling workflow."""

    current_step: WorkflowStep = WorkflowStep.IDLE
    pnr: str | None = None
    surname: str | None = None
    original_flight: FlightInfo | None = None
    alternative_flights: list[FlightInfo] = Field(default_factory=list)
    selected_flight: FlightInfo | None = None
    available_seats: list[SeatOption] = Field(default_factory=list)
    selected_seat: SeatOption | None = None
    change_fee: float = 0.0
    fare_difference: float = 0.0
    transaction_id: str | None = None


@dataclass
class WorkflowDeps:
    """PydanticAI dependency container for workflow state."""

    state: ReschedulingState
