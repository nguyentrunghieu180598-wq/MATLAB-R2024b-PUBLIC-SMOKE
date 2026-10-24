# JTE046 native comparison preparation
Source/software only. No real RSA key, MAT, research CSV, G5 result, or simulation.
W46-A must succeed before real data processing. Scientific G5 never auto-passes.

1. In authorized PRIVATE compute, authenticate existing archives with tested JTE038 decryptor first.
2. Preserve MAT and native Time/Data/IsTimeFirst. Use JTE046_exportNative(records,newPrivateDir).
   Each signal has its own CSV clock. Time-axis normalization is a separate view; original records are unchanged.
   Duplicate timestamps are retained; the exporter does NOT certify their meaning or units.
3. Fill G5_case_manifest_template.json from verified provenance; never guess actual Ambient, units, solver or hashes.
   Rename to manifest.json only when complete. Source MAT must hash-match its GCM receipt member.
   This Python checker validates attested receipt lineage; it does NOT decrypt or independently authenticate GCM.
4. Use linear thermal/filter reconstruction only when justified. 'zoh' means a verified held representation between
   recorded command events; it does NOT mean the memoryless FlwR_calc is a clocked ZOH controller.
   For duplicate times the accepted convention is first_pre_last_post, only after independent verification.
   Unresolved duplicates, >2 event sides, time disorder, extrapolation and unknown sampling block calculation.
5. python jte046_native_compare.py --input /PRIVATE/complete_bundle --output /PRIVATE/new_review.json
   Output must be new and outside input. Keep result/CSV/MAT private.
   Reconstructed threshold crossings are explicitly ESTIMATES, not original solver roots.
   Event time differences require matching before/after transition sequences; no arbitrary nearest matching.
   Integrals are exact for the supplied piecewise representation, not exact physical plant trajectories.
6. Chat independently checks G5, numerical limits and provenance. G6 remains blocked until Chat signs off.
   No inference of pump power from jteUcore; no new bias/load matrix.

Synthetic tests: python test_jte046_native.py; MATLAB JTE046_exportSelftest.
Pipeline tests use mock attestation receipts and bytes explicitly named SYNTHETIC_NOT_MAT. They exercise validators,
not GCM or MATLAB research data. Their temporary outputs are deleted and must not be used as research evidence.
