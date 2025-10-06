from typing import TypedDict, Optional, List

class TravelState(TypedDict, total=False):
    location: Optional[str]
    checkin: Optional[str]
    checkout: Optional[str]
    stay_days: Optional[int]
    adults: Optional[int]
    children: Optional[int]
    rooms: Optional[int]


    ask: Optional[str]
    errors: List[str]
    last_user_msg: Optional[str]
    last_question: Optional[str]
    started: bool