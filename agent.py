"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)
from support import mock_backend

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
EXTRA_TOOLS: List[Dict[str, Any]] = [   # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "hold_time_left",
        "description": (
            "Tell the customer how long they have before a held seat is released. Call "
            "it when the customer asks how much time they have, or before they decide "
            "on a held option and you want to be sure the hold is still live. It reads "
            "the hold made by hold_seat, measured against the same current time the "
            "rest of the system uses. Returns minutes and seconds remaining, or "
            "expired: true when the hold has run out, in which case offer to hold the "
            "seat again. It only reads; it does not extend or create a hold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hold_id": {
                    "type": "string",
                    "description": "The hold_id returned by hold_seat, e.g. HOLD-3FA9C1. Never guess it.",
                },
            },
            "required": ["hold_id"],
        },
    },
]
LOCAL_TOOLS: Dict[str, Any] = {}         # ✏️ Build 2, step 2.1: the functions behind them


def hold_time_left(hold_id: str) -> Dict[str, Any]:
    """Seconds left on a hold, against the backend's own clock."""
    hold = mock_backend._holds.get(hold_id)
    if hold is None:
        return {"error": f"No hold {hold_id}. It was never made, or it has been confirmed."}
    remaining = int((hold["expires_at"] - mock_backend.FIXTURE_CLOCK).total_seconds())
    if remaining <= 0:
        return {"hold_id": hold_id, "expired": True, "seconds_left": 0}
    return {"hold_id": hold_id, "expired": False, "seconds_left": remaining,
            "minutes_left": remaining // 60, "seconds_part": remaining % 60}


LOCAL_TOOLS["hold_time_left"] = hold_time_left


# ── Nine more read-only tools. Each answers one customer question from one file. ──
import json
import re
from support.mock_backend import DATA_DIR, _add_minutes, load_flights, load_policy


def _handbook_sections() -> Dict[str, str]:
    text = (DATA_DIR / "fare_rules_excerpt.md").read_text(encoding="utf-8")
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    return {p.split("\n", 1)[0].strip(): "### " + p.strip() for p in parts}


def next_available_day_tool(origin: str, dest: str, date: str, cabin: str = "Y") -> Dict[str, Any]:
    day = next_available_day(origin, dest, date, cabin)
    return {"origin": origin, "dest": dest, "from_date": date, "cabin": cabin,
            "first_day_with_a_free_seat": day,
            "note": "Counts one passenger only. Use seats_left for a party."}


def fare_rules(topic: str) -> Dict[str, Any]:
    words = [w for w in re.findall(r"[a-z]+", topic.lower()) if len(w) > 3]
    scored = sorted(((sum(s.lower().count(w) for w in words), h, s)
                     for h, s in _handbook_sections().items()), reverse=True)
    hits = [(h, s) for n, h, s in scored if n > 0][:2]
    if not hits:
        return {"error": "Nothing in the Handbook excerpt matches that topic."}
    return {"source": "Handbook v14.3 sections 4 to 7", "sections": [{"heading": h, "text": s} for h, s in hits]}


def reopen_stats(intent_label: str = "") -> Dict[str, Any]:
    rows = [json.loads(l) for l in (DATA_DIR / "transcripts_sample.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if intent_label:
        rows = [r for r in rows if r["intent_label"] == intent_label]
    if not rows:
        return {"error": f"No sampled conversation has intent_label {intent_label!r}."}
    reopened = [r for r in rows if r["reopened_within_72h"]]
    return {"conversations": len(rows), "reopened_within_72h": len(reopened),
            "by_conversation": [{"intent": r["intent_label"], "reopened": r["reopened_within_72h"],
                                 "why": r.get("reopen_reason")} for r in rows],
            "caveat": "Small human-handled sample, not a rate for the whole airline."}


def care_entitlements(policy_row_id: str) -> Dict[str, Any]:
    row = next((r for r in load_policy()["rows"] if r["policy_row_id"] == policy_row_id), None)
    if row is None:
        return {"error": f"No policy row {policy_row_id}. Use the id check_policy returned."}
    return {"policy_row_id": policy_row_id, "care": row["care"], "goodwill": row["goodwill"],
            "handbook_section_6": _handbook_sections().get("6. Care while you wait (per passenger)")}


def cause_in_plain_words(cause_code: str, language: str = "en") -> Dict[str, Any]:
    labels = load_policy()["cause_labels_customer"].get(cause_code)
    if labels is None:
        return {"error": f"Unknown cause_code {cause_code}."}
    return {"cause_code": cause_code, "language": language, "words": labels.get(language, labels["en"])}


def departures_in_window(airport: str, date: str, from_time: str, to_time: str) -> Dict[str, Any]:
    out = []
    for r in load_flights():
        if r["origin"] != airport or r["date"] != date:
            continue
        est = _add_minutes(r["sched_dep_local"], r["delay_min"])
        if r["status"] in ("CANCELLED", "DIVERTED") or not (from_time <= est <= to_time):
            continue
        out.append({"flight_no": r["flight_no"], "dest": r["dest"], "sched_dep": r["sched_dep_local"],
                    "est_dep": est, "status": r["status"], "seats_left_Y": r["seats_left_Y"]})
    return {"airport": airport, "date": date, "window": f"{from_time}-{to_time}",
            "departures": sorted(out, key=lambda x: x["est_dep"])}


def seats_left(flight_no: str, date: str, cabin: str = "Y", party_size: int = 1) -> Dict[str, Any]:
    row = next((r for r in load_flights() if r["flight_no"] == flight_no and r["date"] == date), None)
    if row is None:
        return {"error": f"No flight {flight_no} on {date}."}
    free = row[f"seats_left_{cabin}"]
    return {"flight_no": flight_no, "date": date, "cabin": cabin, "seats_left": free,
            "party_size": party_size, "room_for_party": free >= party_size}


def ground_stop_status(airport: str) -> Dict[str, Any]:
    now = mock_backend.FIXTURE_CLOCK.strftime("%H:%M")
    window = None
    for r in load_flights():
        m = re.search(r"ground stop (\d\d:\d\d)-(\d\d:\d\d)", r["remarks"] or "")
        if m and (r["origin"] == airport or r["dest"] == airport) and "ground stop" in r["remarks"].lower():
            window = m.groups()
    hit = [r["flight_no"] for r in load_flights()
           if "ground stop" in (r["remarks"] or "").lower() and r["date"] == "2025-05-08"
           and airport in (r["origin"], r["dest"])]
    if not window:
        return {"airport": airport, "ground_stop": False, "now_local": now,
                "note": "No ground stop recorded at this airport. Flights here may still be "
                        "delayed by a stop elsewhere; check get_flight_status for the flight."}
    return {"airport": airport, "ground_stop": bool(window) and window[0] <= now < window[1],
            "window_local": window, "now_local": now, "flights_citing_it": len(hit),
            "note": "Taken from flight remarks; the end time is an estimate and can move."}


def what_automation_will_not_do(request: str = "") -> Dict[str, Any]:
    return {"request": request,
            "handbook_section_7": _handbook_sections().get("7. What chat automation will not do")}


def _t(name: str, desc: str, props: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    return {"name": name, "description": desc,
            "input_schema": {"type": "object", "properties": props, "required": required}}


_S = lambda d: {"type": "string", "description": d}
EXTRA_TOOLS.extend([
    _t("next_available_day",
       "Find the first day a customer can fly a route with a free seat, searching from a given "
       "date, for ONE passenger. Use it for 'when is the first day I can fly?'. For a party of "
       "more than one, follow with seats_left on the flight it points to.",
       {"origin": _S("IATA code, e.g. DEN"), "dest": _S("IATA code, e.g. AUS"),
        "date": _S("Date to search from, YYYY-MM-DD"), "cabin": {"type": "string", "enum": ["Y", "J"]}},
       ["origin", "dest", "date"]),
    _t("fare_rules",
       "Look up Larkspur's Handbook (fare families, delay and cancellation rules, care, what chat "
       "will not do) to explain WHY a rule applies, e.g. why there is no hotel. Quote it; do not "
       "invent a rule. It explains rules. check_policy decides what this customer is owed.",
       {"topic": _S("What the customer is asking about, in a few words, e.g. 'hotel weather'")}, ["topic"]),
    _t("reopen_stats",
       "How often a kind of problem came back within 72 hours, from a small sample of human-handled "
       "chats. Use it for 'will this come back?' and say it is a small sample. Leave intent_label "
       "empty for all of them.",
       {"intent_label": _S("e.g. rebook_after_cancellation, refund_vs_credit. Optional.")}, []),
    _t("care_entitlements",
       "What care a customer gets while waiting (meal, hotel, ground, goodwill) for a policy row, "
       "with the Handbook's care table. Needs the policy_row_id from check_policy; call that first.",
       {"policy_row_id": _S("From check_policy, e.g. UNC-CXL")}, ["policy_row_id"]),
    _t("cause_in_plain_words",
       "The customer-facing wording for a delay or cancellation cause code, in English or Spanish. "
       "Use these words, not the raw code (WX, ATC, MX, CREW, SEC).",
       {"cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
        "language": {"type": "string", "enum": ["en", "es"]}}, ["cause_code"]),
    _t("departures_in_window",
       "List flights still leaving an airport between two local times on a date, by estimated "
       "departure (delays included, cancelled and diverted left out). Use it for 'what is still "
       "leaving Denver this afternoon?'.",
       {"airport": _S("IATA code"), "date": _S("YYYY-MM-DD"),
        "from_time": _S("HH:MM, 24-hour local"), "to_time": _S("HH:MM, 24-hour local")},
       ["airport", "date", "from_time", "to_time"]),
    _t("seats_left",
       "Free seats on one flight and date in one cabin, and whether the whole party fits. Use it "
       "before offering a flight to more than one passenger.",
       {"flight_no": _S("e.g. LK419"), "date": _S("YYYY-MM-DD"),
        "cabin": {"type": "string", "enum": ["Y", "J"]},
        "party_size": {"type": "integer", "description": "Passengers on the booking"}},
       ["flight_no", "date"]),
    _t("ground_stop_status",
       "Whether an airport is under a ground stop right now, and until roughly when, from flight "
       "remarks. Use it for 'is Denver still stopped?'. The end time is an estimate; say so.",
       {"airport": _S("IATA code, e.g. DEN")}, ["airport"]),
    _t("what_automation_will_not_do",
       "What this chat is not allowed to do (refunds, hotel approval, groups, minors, partner "
       "flights and similar). Call it when a customer asks for something that may be out of "
       "scope, then hand off with escalate_to_human instead of attempting it.",
       {"request": _S("What the customer asked for, in their words")}, []),
])
LOCAL_TOOLS.update({
    "next_available_day": next_available_day_tool, "fare_rules": fare_rules,
    "reopen_stats": reopen_stats, "care_entitlements": care_entitlements,
    "cause_in_plain_words": cause_in_plain_words, "departures_in_window": departures_in_window,
    "seats_left": seats_left, "ground_stop_status": ground_stop_status,
    "what_automation_will_not_do": what_automation_will_not_do,
})


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        {"role": "user", "content": f"PNR {pnr}, last name {last_name}. {message}"},
    ]

    # Cost goal: cache the start of every request. The tools and the stable
    # instructions are identical on every turn, so they go first and are marked
    # for the cache. The current time changes every second, so it goes AFTER the
    # cached block: at the front it made every request look new and nothing was read back.
    system = [
        {"type": "text", "text": SYSTEM_PROMPT + TONE_ADDENDUM,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": runtime_preamble().strip()},
    ]

    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=system,
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )

    answer = ""
    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        answer = text_of(response)
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=system,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )
        turns += 1

    return text_of(response)


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string", "description": "Flight number as on the booking segment, e.g. LK415."},
                    "date": {"type": "string", "description": "Local departure date of the flight, formatted YYYY-MM-DD (e.g. 2025-05-08). Take it from the booking's disrupted segment, not from today's date."},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": (
                "Find rebooking options for the disrupted segment on this booking: other "
                "Larkspur flights on the same route with enough open seats for everyone on "
                "the PNR, excluding the disrupted flight itself. Call it once the booking "
                "is looked up and the flight is confirmed cancelled, diverted or badly "
                "delayed, before offering the customer any alternative. Each option has an "
                "option_id; that is the value hold_seat and check_policy need. Also returns "
                "an excluded list with reasons, so do not offer flights that appear there."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "Confirmation code of the booking, as given to lookup_booking."}},
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": (
                "Send the customer a written record of something that has already happened "
                "in this conversation, such as a finalized rebooking or an issued voucher. "
                "Call it after that action's tool has returned success, never before and "
                "never for a hold, a pending voucher or an escalation. The message must "
                "state only what the tool results confirmed: flight, times, amounts and "
                "ids, with no promises. The customer receives it, so write it to them."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string", "description": "Confirmation code of the booking the action was taken on."},
                    "message": {"type": "string", "description": "The text sent to the customer, written to them and limited to facts the tool results returned."},
                },
                "required": ["pnr", "message"],
            },
        },
    ]
