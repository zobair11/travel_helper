from state import TravelState
from graph import app
from request_builder import build_search_request, to_pretty_json
from api_client import post_availability, ApiError, preview

def main():
    init_state: TravelState = {"started": False}
    final_state = app.invoke(init_state)

    print("\nCollected Travel Info:")
    for k in ["location", "checkin", "checkout", "adults", "children", "rooms", "lat", "lng"]:
        print(f"{k}: {final_state.get(k)}")

    try:
        payload = build_search_request(final_state, radius_km=20)
        print("\n--- API Request Body ---")
        print(to_pretty_json(payload))

        print("\n--- Calling External API ---")
        result = post_availability(payload)  
        print(preview(result))
    except (ValueError, ApiError) as e:
        print("\nRequest not sent:", e)

if __name__ == "__main__":
    main()