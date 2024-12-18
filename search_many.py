#!/usr/bin/env python3

import random

from pathlib import Path

from search import Search

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

GEOMETRIES = (
    (4, 5),
)

LAYERS = 7

ROOT_PATH = Path('results')

def main():
    if not ROOT_PATH.is_dir():
        ROOT_PATH.mkdir()

    for p, q in GEOMETRIES:
        geo_path = Path(ROOT_PATH, f'{p}_{q}')
        if not geo_path.is_dir():
            geo_path.mkdir()

        max_neighbors = p * (q - 2)

        for _ in range(5):
            rule = random_rule(max_neighbors)

            print(rule.replace(' ', '_'))

if __name__ == '__main__':
    main()
