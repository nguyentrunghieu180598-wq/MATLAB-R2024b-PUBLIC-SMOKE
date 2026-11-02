# WK08 owner decisions (02 Nov 2026, recorded by Claude in the owner's session)

| # | Decision | Owner answer |
|---|---|---|
| a | Scope: sensor sparsity 312/16/8 channels; bias −2 K and −4 K; one +2 K side case; 6 pre-registered closed-loop cases | APPROVED |
| b | Sampled actuator (input ZOH + discrete first-order, a = exp(−Ts/0.001)) replacing the continuous `sensor dynamics 1` TF; Ts = 10 ms reference, 5 ms sensitivity; declared as a model assumption | APPROVED |
| c | Target journal: International Journal of Electric and Hybrid Vehicles (Inderscience; Scopus + WoS ESCI). JTE no longer the target | APPROVED |
| d1 | Writing hold lifted (Methods may be written from week 2) | APPROVED |
| d2 | ONE amended B0L Ts=10 ms 0–340 s pack run, only after WK08 design (Issue #73) passes Claude review; no automatic retry | APPROVED (conditional) |

Six pre-registered cases: (1) 312 ch, hottest-ranked channel −2 K; (2) 312 ch, median-ranked channel −2 K (masking control); (3) 16 sensors −2 K; (4) 16 sensors −4 K; (5) 8 sensors −4 K; (6) 312 ch, hottest-ranked channel +2 K (side case). Channel/subset selection rules are fixed before any bias run, from the accepted baseline only.

Each 2400 s or bias run still needs a per-run owner go-ahead in the session. G5 remains NOT ACCEPTED until the amended baseline is reviewed.
