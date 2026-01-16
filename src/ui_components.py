"""Streamlit UI components for flight rescheduling workflow."""

import streamlit as st

from src.models import RetrievalResult
from src.workflow.models import FlightInfo, SeatOption


def render_flight_cards(flights: list[FlightInfo]) -> str | None:
    """Render flight options as visual cards.

    Returns the selected flight_id if a button is clicked, None otherwise.
    """
    st.markdown("### :airplane: Available Flights")

    selected_flight_id = None
    cols = st.columns(min(len(flights), 3))

    for i, flight in enumerate(flights):
        with cols[i % 3]:
            with st.container(border=True):
                # Flight header with airplane icon
                st.markdown(f"### :airplane: {flight.flight_number}")

                # Departure time as metric
                st.metric(label="Departure", value=flight.departure_time)

                # Route
                st.caption(f"{flight.departure} → {flight.arrival}")

                # Fare difference
                if flight.fare_difference > 0:
                    st.markdown(f":red[+{flight.fare_difference:.0f} TRY]")
                elif flight.fare_difference < 0:
                    st.markdown(f":green[{flight.fare_difference:.0f} TRY]")
                else:
                    st.markdown(":gray[No fare difference]")

                # Select button
                if st.button("Select", key=f"flight_{flight.flight_id}", use_container_width=True):
                    selected_flight_id = flight.flight_id

    return selected_flight_id


def render_seat_cards(seats: list[SeatOption]) -> str | None:
    """Render seat options as visual cards grouped by row type.

    Returns the selected seat_id if a button is clicked, None otherwise.
    """
    st.markdown("### :seat: Available Seats")

    selected_seat_id = None

    # Define row type display order and labels
    row_types = [
        ("extra_legroom", "Extra Legroom", ":star:"),
        ("emergency", "Emergency Exit", ":rotating_light:"),
        ("standard", "Standard", ":seat:"),
    ]

    for row_type, label, icon in row_types:
        type_seats = [s for s in seats if s.row_type == row_type]
        if not type_seats:
            continue

        # Get price for this category
        price = type_seats[0].price
        st.markdown(f"**{icon} {label}** ({price:.0f} TRY)")

        # Display seats in columns (max 6 per row)
        cols = st.columns(min(6, len(type_seats)))
        for i, seat in enumerate(type_seats[:6]):
            with cols[i]:
                # Seat type icon
                if seat.seat_type == "window":
                    seat_icon = ":window:"
                elif seat.seat_type == "aisle":
                    seat_icon = ":door:"
                else:
                    seat_icon = ":seat:"

                with st.container(border=True):
                    st.markdown(f"{seat_icon} **{seat.seat_number}**")
                    st.caption(seat.seat_type.title())

                    if st.button("Select", key=f"seat_{seat.seat_id}", use_container_width=True):
                        selected_seat_id = seat.seat_id

        # Show remaining seats if more than 6
        if len(type_seats) > 6:
            st.caption(f"+{len(type_seats) - 6} more seats available")

    return selected_seat_id


def render_payment_summary(
    fare_difference: float,
    change_fee: float,
    seat_price: float,
    flight: FlightInfo,
    seat: SeatOption,
) -> str | None:
    """Render payment summary with confirmation button.

    Returns the payment method if confirmed, None otherwise.
    """
    st.markdown("### :credit_card: Payment Summary")

    with st.container(border=True):
        st.markdown(f"**New Flight:** {flight.flight_number} at {flight.departure_time}")
        st.markdown(f"**Seat:** {seat.seat_number} ({seat.seat_type.title()})")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("Fare Difference:")
            st.markdown("Change Fee:")
            st.markdown("Seat Selection:")
            st.markdown("**TOTAL:**")
        with col2:
            diff_sign = "+" if fare_difference >= 0 else ""
            st.markdown(f"{diff_sign}{fare_difference:.0f} TRY")
            st.markdown(f"{change_fee:.0f} TRY")
            st.markdown(f"{seat_price:.0f} TRY")
            total = max(0, fare_difference) + change_fee + seat_price
            st.markdown(f"**{total:.0f} TRY**")

    st.markdown("**Select payment method:**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(":credit_card: Credit Card", use_container_width=True):
            return "credit_card"
    with col2:
        if st.button(":moneybag: Klarna", use_container_width=True):
            return "klarna"

    return None


def render_confirmation(transaction_id: str, flight: FlightInfo, seat: SeatOption) -> None:
    """Render booking confirmation message."""
    st.success("Booking Confirmed!")

    with st.container(border=True):
        st.markdown("### :white_check_mark: Your New Booking")
        st.markdown(f"**Flight:** {flight.flight_number}")
        st.markdown(f"**Departure:** {flight.departure_time}")
        st.markdown(f"**Route:** {flight.departure} → {flight.arrival}")
        st.markdown(f"**Seat:** {seat.seat_number} ({seat.seat_type.title()})")
        st.divider()
        st.markdown(f"**Transaction ID:** `{transaction_id}`")
        st.caption("A confirmation email will be sent shortly.")


def _format_source_title(source: str) -> str:
    """Convert source filename to readable title.

    Example: 'ajet_com_en_corporate_rulesandconditions_pet.md' -> 'Pet'
    """
    # Remove file extension and domain prefix
    name = source.replace(".md", "").replace(".txt", "").replace(".pdf", "")

    # Extract last part (usually the topic)
    parts = name.split("_")
    if parts:
        # Get last meaningful part
        title = parts[-1]
        # Convert camelCase/concatenated words
        # Add space before capitals: 'rulesandconditions' stays as is, but we capitalize
        return title.replace("and", " & ").title()

    return source


def render_references(references: list[RetrievalResult] | list[dict]) -> None:
    """Render document references as styled cards with preview.

    Args:
        references: List of RetrievalResult objects or dicts with source, similarity, url, text
    """
    if not references:
        return

    with st.expander(":books: Sources", expanded=False):
        # Collect unique sources (dedupe by URL)
        seen_urls: set[str] = set()
        unique_refs: list[dict] = []

        for ref in references:
            # Handle both RetrievalResult objects and dicts
            if isinstance(ref, dict):
                url = ref.get("url", "")
                source = ref.get("source", "Unknown")
                similarity = ref.get("similarity", 0.0)
                text = ref.get("text", "")
            else:
                url = ref.metadata.get("url", "")
                source = ref.metadata.get("source", "Unknown")
                similarity = ref.similarity
                text = ref.text

            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_refs.append({"url": url, "source": source, "similarity": similarity, "text": text})

        # Display as cards
        for ref_data in unique_refs:
            with st.container(border=True):
                # Title row with similarity badge
                title = _format_source_title(ref_data["source"])
                sim_pct = int(ref_data["similarity"] * 100)

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**:page_facing_up: {title}**")
                with col2:
                    st.caption(f"{sim_pct}% match")

                # Text preview
                preview = ref_data["text"][:150].replace("\n", " ")
                if len(ref_data["text"]) > 150:
                    preview += "..."
                st.caption(preview)

                # URL link
                st.markdown(f":link: [{ref_data['url']}]({ref_data['url']})")
