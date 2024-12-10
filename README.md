# Hypergol
Author: Evan Day

## Overview

**Hypergol** is a cellular automata simulator for non-Euclidean hyperbolic regular tilings.

## Building

Hypergol's required libraries can be found in `requirements.txt`. To easily install these into a Python virtual environment, run the following commands.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage

Hypergol is built as a Python package and can be run with `python3 -m hypergol`.

```bash
$ python3 -m hypergol --help
usage: hypergol [-h] [-l LAYERS] p q

Hyperbolic cellular automata simulator

positional arguments:
  p                     number of sides to a polygon
  q                     number of polygons around a vertex

options:
  -h, --help            show this help message and exit
  -l LAYERS, --layers LAYERS
                        number of layers to initially generate. default: 5
```
