#!/usr/bin/env python3

import random
import signal
import sys
import os

from pathlib import Path
from types import SimpleNamespace

from search import Search

ROOT_PATH = Path('results')
GEOMETRIES = (
    (4, 5),
)
RUNNING = True

def random_rule(max_neighbors):
    born = set()
    survive = set()

    for i in range(max_neighbors + 1):
        for collection in (born, survive):
            if random.choice([True, False]):
                collection.add(i)

    return ' '.join((
        'b',
        ' '.join(str(i) for i in born),
        's',
        ' '.join(str(i) for i in survive)
    ))

def run_search(config):
    rule, p, q, seed = config

    outfile = Path(ROOT_PATH, f'{p}_{q}', rule.replace(' ', '_'), str(seed))

    if outfile.exists():
        return

    if not outfile.parent.is_dir():
        outfile.parent.mkdir(parents=True)

    print(outfile)

    with outfile.open('w') as fp:
        search = Search(rule, p, q, seed, layers=6, file=fp)
        search.print_config()
        search.run()

def config_generator():
    while RUNNING:
        p, q = random.choice(GEOMETRIES)
        max_neighbors = p * (q - 2)
        rule = random_rule(max_neighbors)
        for _ in range(3):
            if not RUNNING:
                break
            seed = random.randrange(2 ** 64)
            yield (rule, p, q, seed)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--jobs', type=int, default=4)

    args = parser.parse_args()

    children = set()
    max_children = args.jobs

    def graceful_shutdown(signum, frame):
        global RUNNING
        if RUNNING:
            RUNNING = False
            os.write(sys.stdout.fileno(), b'Stopping after current jobs finish. Press Ctrl + C again to force quit.')
        else:
            for child in children:
                os.kill(child, signal.SIGKILL)
            sys.exit(0)

    signal.signal(signal.SIGINT | signal.SIGTERM, graceful_shutdown)

    for config in config_generator():
        if len(children) == max_children:
            while True:
                if not RUNNING:
                    break

                pid, status = os.waitpid(0, os.WNOHANG)
                if (pid, status) != (0, 0):
                    break

            if not RUNNING:
                break

            children.remove(pid)

        while RUNNING and len(children) < max_children:
            pid = os.fork()
            if pid == 0:
                # child process
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                run_search(config)
                sys.exit(0)
            else:
                children.add(pid)

    for child in children:
        os.waitpid(child, 0)

if __name__ == '__main__':
    main()
