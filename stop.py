import os
import psutil
import capture

PROCNAME = "arducam"

proc_ids = []
with open(os.path.join(capture._PATH, 'running.info'), 'r') as f:
    for line in f.readlines():
        proc_ids.append(int(line.rstrip()))

for proc in psutil.process_iter():
    for running_id in proc_ids:
        if proc.pid == running_id:
            print(proc.name())
            proc.kill()