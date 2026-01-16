"""Hardcoded flight, booking, and seat data for demo purposes."""

from src.workflow.models import FlightInfo, SeatOption

# Hardcoded bookings (PNR -> booking details)
BOOKINGS: dict[str, dict] = {
    "ABC123": {
        "surname": "SMITH",
        "flight": FlightInfo(
            flight_id="orig1",
            flight_number="AJ101",
            departure="IST",
            arrival="AYT",
            departure_time="14:00",
            fare_class="W",  # Economy
            fare_difference=0.0,
        ),
    },
    "XYZ789": {
        "surname": "DOE",
        "flight": FlightInfo(
            flight_id="orig2",
            flight_number="AJ201",
            departure="SAW",
            arrival="ESB",
            departure_time="16:00",
            fare_class="P",  # Basic
            fare_difference=0.0,
        ),
    },
    "DEF456": {
        "surname": "JOHNSON",
        "flight": FlightInfo(
            flight_id="orig3",
            flight_number="AJ301",
            departure="IST",
            arrival="AYT",
            departure_time="10:00",
            fare_class="Y",  # Premium
            fare_difference=0.0,
        ),
    },
}

# Alternative flights by route (departure-arrival)
ALTERNATIVES: dict[str, list[FlightInfo]] = {
    "IST-AYT": [
        FlightInfo(
            flight_id="f1",
            flight_number="AJ103",
            departure="IST",
            arrival="AYT",
            departure_time="18:00",
            fare_class="W",
            fare_difference=150.0,
        ),
        FlightInfo(
            flight_id="f2",
            flight_number="AJ105",
            departure="IST",
            arrival="AYT",
            departure_time="20:00",
            fare_class="W",
            fare_difference=50.0,
        ),
        FlightInfo(
            flight_id="f3",
            flight_number="AJ107",
            departure="IST",
            arrival="AYT",
            departure_time="22:00",
            fare_class="W",
            fare_difference=-100.0,
        ),
    ],
    "SAW-ESB": [
        FlightInfo(
            flight_id="f4",
            flight_number="AJ203",
            departure="SAW",
            arrival="ESB",
            departure_time="19:00",
            fare_class="P",
            fare_difference=100.0,
        ),
        FlightInfo(
            flight_id="f5",
            flight_number="AJ205",
            departure="SAW",
            arrival="ESB",
            departure_time="21:00",
            fare_class="P",
            fare_difference=0.0,
        ),
    ],
}

# Seat maps by flight_id
SEATS: dict[str, list[SeatOption]] = {
    "f1": [
        # Extra legroom (rows 1-2)
        SeatOption(seat_id="s1a", seat_number="1A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s1b", seat_number="1B", seat_type="middle", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s1c", seat_number="1C", seat_type="aisle", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s2a", seat_number="2A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s2c", seat_number="2C", seat_type="aisle", price=400.0, row_type="extra_legroom"),
        # Emergency exit (row 11)
        SeatOption(seat_id="s11a", seat_number="11A", seat_type="window", price=350.0, row_type="emergency"),
        SeatOption(seat_id="s11c", seat_number="11C", seat_type="aisle", price=350.0, row_type="emergency"),
        # Standard (rows 12-15)
        SeatOption(seat_id="s12a", seat_number="12A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12b", seat_number="12B", seat_type="middle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12c", seat_number="12C", seat_type="aisle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s14a", seat_number="14A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s14c", seat_number="14C", seat_type="aisle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s15b", seat_number="15B", seat_type="middle", price=99.0, row_type="standard"),
    ],
    "f2": [
        SeatOption(seat_id="s1a_f2", seat_number="1A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s1c_f2", seat_number="1C", seat_type="aisle", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s11a_f2", seat_number="11A", seat_type="window", price=350.0, row_type="emergency"),
        SeatOption(seat_id="s12a_f2", seat_number="12A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12c_f2", seat_number="12C", seat_type="aisle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s13a_f2", seat_number="13A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s13c_f2", seat_number="13C", seat_type="aisle", price=99.0, row_type="standard"),
    ],
    "f3": [
        SeatOption(seat_id="s1a_f3", seat_number="1A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s12a_f3", seat_number="12A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12c_f3", seat_number="12C", seat_type="aisle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s14b_f3", seat_number="14B", seat_type="middle", price=99.0, row_type="standard"),
    ],
    "f4": [
        SeatOption(seat_id="s1a_f4", seat_number="1A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s12a_f4", seat_number="12A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12c_f4", seat_number="12C", seat_type="aisle", price=99.0, row_type="standard"),
    ],
    "f5": [
        SeatOption(seat_id="s1a_f5", seat_number="1A", seat_type="window", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s1c_f5", seat_number="1C", seat_type="aisle", price=400.0, row_type="extra_legroom"),
        SeatOption(seat_id="s12a_f5", seat_number="12A", seat_type="window", price=99.0, row_type="standard"),
        SeatOption(seat_id="s12c_f5", seat_number="12C", seat_type="aisle", price=99.0, row_type="standard"),
        SeatOption(seat_id="s15a_f5", seat_number="15A", seat_type="window", price=99.0, row_type="standard"),
    ],
}

# Change fees based on fare class (from AJet fare rules)
# Key: fare_class, Value: change fee in TRY (None = not allowed)
CHANGE_FEES: dict[str, float | None] = {
    "U": None,  # Not allowed
    "W": 600.0,  # Economy - assuming within 12 hours
    "P": 600.0,  # Basic - assuming within 12 hours
    "V": 600.0,  # Economy restricted
    "Y": 0.0,  # Premium - no change fee
}


def get_change_fee(fare_class: str) -> float | None:
    """Get change fee for a fare class."""
    return CHANGE_FEES.get(fare_class.upper(), 600.0)


def lookup_booking(pnr: str, surname: str) -> dict | None:
    """Look up a booking by PNR and surname."""
    booking = BOOKINGS.get(pnr.upper())
    if booking and booking["surname"] == surname.upper():
        return booking
    return None


def get_alternative_flights(departure: str, arrival: str) -> list[FlightInfo]:
    """Get alternative flights for a route."""
    route_key = f"{departure.upper()}-{arrival.upper()}"
    return ALTERNATIVES.get(route_key, [])


def get_seats_for_flight(flight_id: str) -> list[SeatOption]:
    """Get available seats for a flight."""
    return SEATS.get(flight_id, [])
