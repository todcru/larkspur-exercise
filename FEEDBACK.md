# Client review: Larkspur disruption-care agent

**To:** Room 9  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-19 04:56

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. agent.py EXTRA_TOOLS defines hold_time_left twice, and the scan counts 10 schemas where the pack ships 9.**

build_tools() returns nine schemas, and the scan lists hold_time_left among them at 495 characters. Your EXTRA_TOOLS list adds a second schema named hold_time_left, then extends with eight more. tool_list() returns build_tools() + EXTRA_TOOLS on every turn. The request therefore carries two tools with the same name and different descriptions, and nothing in the repository shows which one Claude receives or whether the API accepts the call.

Run python3 run.py --show-tools and paste the full list, so the duplicate hold_time_left entries are visible.

**2. agent.py EXTRA_TOOLS grows from 1 to 10 tools, and no run shows whether the model picks the right one.**

Your diff adds hold_time_left plus nine more: fare_rules, reopen_stats, care_entitlements, cause_in_plain_words, departures_in_window, seats_left, ground_stop_status, what_automation_will_not_do, next_available_day. Every one of them is offered on every turn alongside the nine shipped tools. Several overlap: next_available_day and seats_left, care_entitlements and check_policy, fare_rules and what_automation_will_not_do. A larger model sees the same overlapping menu, and no trace in this repository shows how selection behaves with it.

Run python3 run.py --all --trace and paste the totals footer, then run python3 run.py --tool-tax and paste its output.

**3. agent.py run_agent() has a loop edit that changes what the model sees, and no before and after exists for it.**

Your diff changes the assistant message from text_of(response) to response.content and returns text_of(response) after the loop. The scan confirms a while loop that tests stop_reason == tool_use, with MAX_TOOL_CALLS at 8. There is no readout-trace.json and no committed run, so the effect of this edit on any booking is unrecorded. If a booking reaches 8 turns, the loop exits with whatever the last response held, and nothing here shows how often that happens.

Run python3 run.py --all --trace and paste the per-booking turn counts, naming any that reach 8.

**4. The 13 files that differ from the pack, including verify.py, eval_harness.py and bench.py, change what any number from them means.**

The scan lists verify.py, eval_harness.py, bench.py, readout.py, run.py and the whole support/ directory as differing from the shipped pack. You were asked not to edit them. A pass from python3 verify.py or a delta from bench.py comes from modified instruments, so a sponsor cannot be told it measures the same thing it measures elsewhere.

Restore the given files from the pack, rerun python3 verify.py 1.2, and paste the output.

**5. No evals/cases.json and no readout-trace.json exist, and TONE_ADDENDUM is 0 characters.**

The repository has no eval cases and no committed wire run, so there is no number here for any claim about the agent. TONE_ADDENDUM is still empty, so the system prompt is the shipped SYSTEM_PROMPT plus runtime_preamble() and nothing from you. Any answer to Priya's model question currently has no measurement under it, and a bigger model would not supply the missing eval cases or fix the duplicate tool name.

Run python3 bench.py --label before --stage 1 --runs 3, make one change, run it again with --label after, then paste the output of python3 bench.py --compare before after.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (453 lines)`
- `PITCH.md`
- `TEAM.md`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
