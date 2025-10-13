from state import TravelState
from graph import app
from request_builder import build_search_request, to_pretty_json
from api_client import post_availability, ApiError
from hotel_result_mapper import map_hotelbeds_payload
from customer_result_format import format_customer_list
from hotel_ranking import top_n_cheapest
from cache_store import init_redis, get_cached_result, set_cached_result
from hotel_result_mapper import HotelList, HotelItem


def main():
    print("Initializing services...")
    
    init_state: TravelState = {"started": False}
    final_state = app.invoke(init_state)

    print("\nCollected Travel Info:")
    for k in ["location", "checkin", "checkout", "adults", "children", "rooms", "lat", "lng"]:
        print(f"{k}: {final_state.get(k)}")

    request_data = {
        "lat": final_state.get("lat"),
        "lng": final_state.get("lng"),
        "checkin": final_state.get("checkin"),
        "checkout": final_state.get("checkout"),
        "adults": final_state.get("adults"),
        "children": final_state.get("children"),
        "rooms": final_state.get("rooms"),
    }

    cached = get_cached_result(request_data)
    if cached:
        mapped = HotelList(hotels=[HotelItem(**h) for h in cached])
    else:
        try:
            payload = build_search_request(final_state, radius_km=20)
            print("\n--- API Request Body ---")
            print(to_pretty_json(payload))

            print("\n--- Calling External API ---")
            api_response = post_availability(payload)

            mapped = map_hotelbeds_payload(api_response)

            hotels_dicts = [h.model_dump() for h in mapped.hotels]
            set_cached_result(request_data, hotels_dicts)

        except (ValueError, ApiError) as e:
            print("Request failed:", e)
            return

    cheapest = top_n_cheapest(mapped.hotels, 10)

    print(f"\nTotal mapped hotels: {len(mapped.hotels)}")
    print(f"Showing top {len(cheapest)} cheapest:\n")

    print(format_customer_list(cheapest))  

if __name__ == "__main__":
    main()
