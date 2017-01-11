#!/usr/bin/python

import argparse
import collections
import os

parser = argparse.ArgumentParser(description='Protocol Input Vs. Output Tester')
parser.add_argument('number', type=int, default=1, help='number of fudge dice')
args = parser.parse_args()

