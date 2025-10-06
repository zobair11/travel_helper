from state import TravelState
from graph import app

def main():
    init_state: TravelState = {"started": False}
    final_state = app.invoke(init_state)

    print("\nCollected Travel Info:")
    for k in ["location", "checkin", "checkout", "adults", "children", "rooms"]:
        print(f"{k}: {final_state.get(k)}")

if __name__ == "__main__":
    main()
