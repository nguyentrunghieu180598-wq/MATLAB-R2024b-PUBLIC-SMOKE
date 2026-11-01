# WK07 owner approval: one new nonbattery R2024b U10 CI trial (01 Nov 2026, 22:38 ICT)

The project owner approved, in the Claude session, exactly ONE new GitHub Actions trial of the amended synthetic fixture (PR #72), after the WK06 allowance was consumed by run 41319712018. Same limits as Issue #67: synthetic `WK04T0Nonbattery` model only, no battery pack, no B0L340 use, no public private data, no automatic rerun.

- Fresh one-shot intent name `WK07_MATLAB_ATTEMPT_INTENT_20261101.json` (the WK06 intent stays and is not reused).
- Trigger message `WK07_NONBATTERY_ONE_SHOT_20261101`, marker `jte-public/WK07_MATLAB_TRIGGER.txt`, S→E→T chain unchanged.
- Basis: owner-local full dry run of `45a8f91` reached `stage=DONE` (diagnostic only).
- A PASS qualifies the nonbattery API toy only. G-M3 and G5 remain UNQUALIFIED.
