# Client review: Larkspur disruption-care agent

**To:** Room 9  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-19 05:15

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

**1. agent.py search_alternatives went from the 6-character description "search" to 328 characters that name its place in the call order.**

The new text says "Use it after get_flight_status shows a delay or cancellation that needs rebooking, and before hold_seat" and that the option_id feeds hold_seat and check_policy (chosen_option_id). The pnr property now carries "Confirmation code from lookup_booking, e.g. K7PQ2M". That is what a sponsor can hear as a measured change to what the model is told, and nothing in the repository ties it to a result yet.

Run python3 bench.py --label before --stage 1 --runs 3 on the shipped template, the same on this build as after, then paste the output of python3 bench.py --compare before after.

**2. PITCH.md Number reads "4 of 7 cases passed (57%)" with "1 run each", and there is no readout-trace.json behind it.**

Seven cases at one run each makes a single flipped case worth 14 points. The Number line has no before figure, so nothing in the repository says what this build improved on. No wire run of the agent survived the push.

Run python3 eval_harness.py three times and paste the per-case pass counts, then python3 run.py --all --trace and paste the totals footer.

**3. agent.py hold_seat still has the 73-character description "Place a 15-minute hold on one alternative. Reversible. It simply expires."**

Every other tool in the file has 216 characters or more except this one. hold_seat sits between search_alternatives and confirm_rebooking, and your pitch says the next fix is that a missed-connection claim is checked against the booking records before a seat is held. Its pnr and option_id properties carry no description at all, and conn-0101 and irrv-0101 both pass through this tool.

Run python3 run.py T9WN4C --trace and paste the hold_seat call with the arguments the model supplied.

**4. Your own target, tone-0101, fails with TONE_ADDENDUM at 0 characters and no diff line touching the system prompt.**

PITCH.md names the failure: the agent "issues a voucher and gives a full rundown to an angry customer who threatens legal action". The system prompt in run_agent() is still runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM with an empty addendum. No tool description in your diff mentions abuse or legal threats. So the fix you name under Next has no edit in this diff yet. Look at where a larger model would and would not help: the cause you can see is missing instruction and no tool-side gate on issue_voucher, and the model name appears nowhere in that path.

Run python3 run.py R8KD3F --trace and paste the turn where issue_voucher is called, with the policy_row_id it passed.

**5. evals/cases.json shows 7 cases, 5 hard gates, and 5 of the first 7 entries still carry the author "<your name>".**

Only team-0101 and conn-0101 show "Suprava" as author. The readme says gate 3.1 looks for your name on at least one case, and a pod with one author has one person's judgement in it. Separately, the harness, verify.py, bench.py and readout.py all differ from the shipped pack, so the 57% was produced by files the team was asked not to edit.

Run python3 verify.py 3.1 and paste its output, then restore the given harness files and rerun python3 eval_harness.py so the 4 of 7 comes from the shipped grader.

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

- `agent.py (238 lines)`
- `PITCH.md`
- `TEAM.md`
- `evals/cases.json`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
