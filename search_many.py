#!/usr/bin/env python3

import random
import signal
import sys
import os
import argparse

from pathlib import Path
from types import SimpleNamespace

from search import Search

ROOT_PATH = Path('smallset2')
GEOMETRIES = (
    (3, 7),
    (4, 5),
    (5, 4),
    (6, 4),
    (7, 3),
    (8, 3),
)
RUNNING = True

def random_rule(max_neighbors):
    born = set()
    survive = set()

    # being born on 0 neighbors is BORING
    for i in range(1, max_neighbors + 1):
        if random.choice([True, False]):
            born.add(i)

    for i in range(max_neighbors + 1):
        if random.choice([True, False]):
            survive.add(i)

    return ' '.join((
        'b',
        ' '.join(map(str, sorted(born))),
        's',
        ' '.join(map(str, sorted(survive))),
    ))

def run_search(config):
    rule, p, q, layers, seed, init_prob, init_limit = config

    outfile = Path(ROOT_PATH, f'{p}_{q}', rule.replace(' ', '_'), str(seed))

    print(outfile)

    outfile.parent.mkdir(parents=True, exist_ok=True)

    with outfile.open('w') as fp:
        search = Search(rule, p, q, layers, seed, file=fp, init_prob=init_prob, init_limit=init_limit)
        search.print_config()
        search.run()

def config_generator(layers, init_prob, init_limit):
    while RUNNING:
        geometry = random.choice(GEOMETRIES)
        p, q = geometry
        max_neighbors = p * (q - 2)
        rule = random_rule(max_neighbors)

        for _ in range(3):
            if not RUNNING:
                break
            seed = random.randrange(2 ** 64)
            yield (rule, p, q, layers, seed, init_prob, init_limit)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--jobs', type=int, default=4)
    parser.add_argument('-l', '--layers', help='number of layers to initially generate. default: 5', type=int, required=False, default=5)
    parser.add_argument('-p', '--init-prob', help='probability of making a cell alive during random automaton initialization. default: 0.5',
                        type=float, default=0.5)
    parser.add_argument('-n', '--init-limit', help='limit number of cells to randomize at initialization', type=int)

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

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    for config in config_generator(args.layers, args.init_prob, args.init_limit):
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

        if RUNNING and len(children) < max_children:
            pid = os.fork()
            if pid == 0:
                # child process
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                run_search(config)
                sys.exit(0)
            else:
                children.add(pid)

    for child in children:
        os.waitpid(child, 0)

if __name__ == '__main__':
    main()
