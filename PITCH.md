# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: A Claude tool-loop agent for Larkspur disruption chats, with 19 tools: the 9 given plus 10 we added (hold_time_left, seats_left, ground_stop_status and others).
Does: Looks up the booking, checks flight status and policy, offers rebooking options, holds a seat for 15 minutes, and hands out-of-scope cases (groups, refunds) to a human.
Number: 7 of 8 eval cases pass (88%), n=8 cases, 1 run each, and 4 of the 5 hard-gate cases pass.
Safety check: The agent cannot confirm a rebooking itself; confirm_rebooking needs the customer's own Confirm click, and the irreversible-action hard gate passes.
Next: Add a TONE_ADDENDUM so abusive or legal-threat messages escalate to a human instead of getting a normal entitlements rundown.
Still broken: An abusive message with a legal threat (tone-0101) gets a normal rundown and a voucher instead of an escalation to a human.
Lever: intelligence

## Priya asked

Costs:
Wrong:
Runs it:
Left out:
