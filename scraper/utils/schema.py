VALID_STATUSES = {"active", "coming_soon", "closed"}
VALID_MODALITIES = {
    "cold_plunge", "sauna_traditional", "sauna_infrared", "contrast",
    "red_light", "compression", "breathwork", "float", "cryo", "iv",
}
VALID_FORMATS = {"private_suite", "communal", "both"}
VALID_SESSION_STYLES = {"guided_social", "free_flow", "both"}
VALID_ACCESS = {"day_pass", "membership_only", "both"}
VALID_AMENITIES = {"showers", "towels_provided", "parking", "lockers"}

EMPTY_STUDIO = {
    "id": None,
    "name": None,
    "metro": None,
    "city": None,
    "lat": None,
    "lng": None,
    "status": "active",
    "brand": None,
    "state": None,
    "neighborhood": None,
    "address": None,
    "website": None,
    "booking_url": None,
    "instagram": None,
    "modalities": [],
    "plunge_temp_f_min": None,
    "plunge_temp_f_max": None,
    "format": None,
    "session_style": None,
    "access": None,
    "day_pass_price_usd": None,
    "membership_from_usd": None,
    "amenities": [],
    "google_place_id": None,
    "google_rating": None,
    "google_reviews_count": None,
    "source_urls": [],
    "last_verified": None,
}
