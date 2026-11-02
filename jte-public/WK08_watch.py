"""External one-shot limits. Source only; MATLAB starts only via reviewed workflow."""
import json
import os
from pathlib import Path
import shutil
import time
from BTMS_M3_oneShotWatchdog import atomic, memory, proc_start, proc_rss, terminate_tree

ROOT = Path('actuator-review-private')
GiB = 1024**3
TARGET = None


def monitor():
    global TARGET
    started = time.monotonic()
    identity = None
    pid = None
    peak = 0
    atomic(ROOT / 'WK08_WATCH_READY.json', {'ready': True})
    with (ROOT / 'WK08_RESOURCES.jsonl').open('a') as log:
        while not (ROOT / 'WK08_DONE.json').exists():
            reason = None
            if pid is None and (ROOT / 'WK08_PID.json').is_file():
                data = json.loads((ROOT / 'WK08_PID.json').read_text())
                pid = int(data['pid'])
                assert pid > 1 and pid != os.getpid()
                assert b'MATLAB' in Path(f'/proc/{pid}/cmdline').read_bytes() or b'matlab' in Path(f'/proc/{pid}/cmdline').read_bytes()
                identity = proc_start(pid)
                TARGET = (pid, identity)
                atomic(ROOT / 'WK08_WATCH_ACK.json', {'pid': pid, 'start': identity})
                started = time.monotonic()
            mem = memory()
            if mem['hostAvailable'] < 2*GiB or (mem['cgroupAvailable'] is not None and mem['cgroupAvailable'] < 2*GiB):
                reason = 'RAM_RESERVE'
            sizes = [p.stat().st_size for p in ROOT.rglob('*') if p.is_file()]
            if shutil.disk_usage(ROOT).free < 2*GiB:
                reason = 'DISK_RESERVE'
            if max(sizes, default=0) > GiB or sum(sizes) > 2*GiB:
                reason = 'PAYLOAD_CAP'
            if time.monotonic()-started > (1200 if pid else 300):
                reason = 'WALL_LIMIT'
            if pid:
                try:
                    assert proc_start(pid) == identity
                    peak = max(peak, proc_rss(pid))
                except FileNotFoundError:
                    reason = 'MATLAB_EXIT_WITHOUT_DONE'
            log.write(json.dumps({'elapsed_s': time.monotonic()-started, 'RAM': mem,
                                  'peakRSS_bytes': peak, 'payload_bytes': sum(sizes), 'reason': reason})+'\n')
            log.flush()
            if reason:
                atomic(ROOT / 'WK08_WATCH_STOP.json', {'reason': reason, 'peakRSS_bytes': peak})
                if pid:
                    terminate_tree(pid, identity)
                return
            time.sleep(1)


if __name__ == '__main__':
    try:
        monitor()
    except Exception:
        atomic(ROOT / 'WK08_WATCH_STOP.json', {'reason': 'WATCHDOG_UNQUALIFIED'})
        if TARGET:
            terminate_tree(*TARGET)
        raise SystemExit(1)
