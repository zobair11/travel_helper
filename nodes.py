import re
import json
from datetime import datetime
from typing import Any

from state import TravelState
from config import input_llm, validator_llm, DATE_FMT, REQUIRED_FIELDS
from prompts import INPUT_AGENT_SYS, VALIDATOR_AGENT_SYS
from utils import parse_int_like, ask_json, ensure_checkout


def start_or_prompt(state: TravelState) -> TravelState:
    """
    Start node: if not started, ask for the initial travel request.
    """
    if not state.get("started"):
        msg = input("Enter your travel request: ")
        state["last_user_msg"] = msg
        state["started"] = True
    return state


def input_agent_node(state: TravelState) -> TravelState:
    collected = {
        "location": state.get("location"),
        "checkin": state.get("checkin"),
        "checkout": state.get("checkout"),
        "stay_days": state.get("stay_days"),
        "adults": state.get("adults"),
        "children": state.get("children"),
        "rooms": state.get("rooms")
    }
    user_input = state.get("last_user_msg") or ""

    ia_user = f'''User input: "{user_input}"
Current collected: {json.dumps(collected, ensure_ascii=False)}
Return JSON ONLY.'''

    ia = ask_json(
        input_llm,
        INPUT_AGENT_SYS,
        ia_user,
        fallback={"ask": None, "update_fields": {}}
    )

    for k, v in ia.get("update_fields", {}).items():
        if k in collected:
            state[k] = v

    state["ask"] = ia.get("ask")
    return state


def wait_for_user_node(state: TravelState) -> TravelState:
    q = state.get("ask") or "Please provide more details:"
    answer = input(q + " ")
    state["last_user_msg"] = answer
    state["last_question"] = q
    state["ask"] = None
    return state


def map_user_answer_node(state: TravelState) -> TravelState:
    answer = state.get("last_user_msg") or ""
    last_q = (state.get("last_question") or "").lower()

    updated = False

    if re.search(r"\badults?\b", last_q) or re.search(r"\brooms?\b", last_q) or re.search(r"\bchild(ren)?\b", last_q):
        m_adults = re.search(r"(\d+)\s*adults?", answer, flags=re.I)
        m_rooms  = re.search(r"(\d+)\s*rooms?",  answer, flags=re.I)
        m_kids   = re.search(r"(\d+)\s*child(?:ren)?", answer, flags=re.I)

        if m_adults:
            state["adults"] = max(1, int(m_adults.group(1))); updated = True
        if m_rooms:
            state["rooms"] = max(1, int(m_rooms.group(1)));   updated = True
        if m_kids:
            state["children"] = max(0, int(m_kids.group(1))); updated = True

        if updated:
            return state

    n = parse_int_like(answer)
    if n is not None:
        if re.search(r"\badults?\b", last_q) and state.get("adults") in (None, ""):
            state["adults"] = max(1, n); return state
        if re.search(r"\brooms?\b", last_q) and state.get("rooms") in (None, ""):
            state["rooms"] = max(1, n); return state
        if re.search(r"\bchild(ren)?\b", last_q):
            state["children"] = max(0, n); return state

    collected = {
        "location": state.get("location"),
        "checkin": state.get("checkin"),
        "checkout": state.get("checkout"),
        "stay_days": state.get("stay_days"),
        "adults": state.get("adults"),
        "children": state.get("children"),
        "rooms": state.get("rooms"),
    }

    map_resp = ask_json(
        input_llm,
        INPUT_AGENT_SYS,
        (
            f'Previous question: "{state.get("last_question")}"\n'
            f'User just answered: "{answer}"\n'
            f'Current collected: {json.dumps(collected, ensure_ascii=False)}\n'
            'Update ONLY the field(s) that were asked, in "update_fields".'
        ),
        fallback={"ask": None, "update_fields": {}}
    )

    for k, v in map_resp.get("update_fields", {}).items():
        if k in ["location", "checkin", "checkout", "stay_days", "adults", "children", "rooms"]:
            state[k] = v
    return state


def validator_node(state: TravelState) -> TravelState:
    collected = {
        "location": state.get("location"),
        "checkin": state.get("checkin"),
        "checkout": state.get("checkout"),
        "stay_days": state.get("stay_days"),
        "adults": state.get("adults"),
        "children": state.get("children"),
        "rooms": state.get("rooms")
    }

    v = ask_json(
        validator_llm,
        VALIDATOR_AGENT_SYS,
        f"Fields to validate: {json.dumps(collected, ensure_ascii=False)}\nReturn JSON ONLY.",
        fallback={"clean_fields": collected, "errors": [], "ask": None}
    )

    cf = v.get("clean_fields", {}) or {}

    norm_checkin, norm_checkout = ensure_checkout(
        cf.get("checkin"), cf.get("checkout"), cf.get("stay_days")
    )
    if norm_checkin:
        cf["checkin"] = norm_checkin
    if norm_checkout:
        cf["checkout"] = norm_checkout

    ra = cf.get("adults")
    if ra is not None and str(ra).strip() != "":
        try:
            cf["adults"] = max(1, int(str(ra).strip()))
        except Exception:
            cf["adults"] = None

    rc = cf.get("children")
    if rc in (None, "", "null"):
        cf["children"] = 0
    else:
        try:
            cf["children"] = max(0, int(str(rc).strip()))
        except Exception:
            cf["children"] = 0

    rr = cf.get("rooms")
    if rr is not None and str(rr).strip() != "":
        try:
            cf["rooms"] = max(1, int(str(rr).strip()))
        except Exception:
            cf["rooms"] = None

    errors = list(v.get("errors", []))
    if cf.get("checkin") and cf.get("checkout"):
        try:
            dci = datetime.strptime(cf["checkin"], DATE_FMT)
            dco = datetime.strptime(cf["checkout"], DATE_FMT)
            if not (dci < dco):
                errors.append("Checkout must be after checkin.")
        except Exception:
            errors.append("Invalid date format; expected YYYY-MM-DD.")


    def is_missing(name: str, val: Any) -> bool:
        if name in ("adults", "rooms"):
            return val is None
        return val is None or (isinstance(val, str) and not val.strip())

    missing = [f for f in REQUIRED_FIELDS if is_missing(f, cf.get(f))]

    ask = v.get("ask")
    if missing and not ask:
        m = missing[0]
        ask = (
            "What city (and country) are you traveling to?" if m == "location" else
            "What is your check-in date? (YYYY-MM-DD)" if m == "checkin" else
            "What is your check-out date? (YYYY-MM-DD)" if m == "checkout" else
            "How many adults and children will be staying?" if m == "adults" else
            "How many rooms will you need?" if m == "rooms" else
            None
        )


    for k in ["location", "checkin", "checkout", "stay_days", "adults", "children", "rooms"]:
        state[k] = cf.get(k)

    state["errors"] = errors
    state["ask"] = ask
    return state
