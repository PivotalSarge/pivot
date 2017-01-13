#!/usr/bin/python

import argparse
import difflib
import os
import subprocess
import sys

def file_to_hex_string(path):
    str = ''
    with open(path, 'rb') as f:
        byte = f.read(1)
        while byte:
            str += '{:02x}'.format(ord(byte[0]))
            byte = f.read(1)
    return str

def enforce_byte_boundaries(i, j, n):
    # print('i={0} j={1} n={2}'.format(i, j, n))
    golden_idx = i
    golden_len = n
    if 0 != (golden_idx % 2):
        golden_idx -= 1
        golden_len += 1
    if 0 != (golden_len % 2):
        golden_len -= 1

    actual_idx = j
    actual_len = n
    if 0 != (actual_idx % 2):
        actual_idx -= 1
        actual_len += 1
    if 0 != (actual_len % 2):
        actual_len -= 1

    # print('gi={0} gl={1} ai={2} al={3}'.format(golden_idx, golden_len, actual_idx, actual_len))
    return golden_idx, golden_len, actual_idx, actual_len

parser = argparse.ArgumentParser(description='Protocol Input Vs. Output Tester')
parser.add_argument('--pivot_home', default=os.path.dirname(os.path.realpath(__file__)), help='Home of pivot')
parser.add_argument('--proto_home', default=os.path.dirname(os.path.realpath(__file__)), help='Home of protocol')
parser.add_argument('--tests', nargs='+', help='Names of tests to run')
parser.add_argument('--test_driver', default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dummy.sh'), help='Path to test driver executable')
args = parser.parse_args()

if not os.path.isdir(args.pivot_home):
    print('{0} is not a directory.'.format(args.pivot_home))
    sys.exit(1)

if not os.path.isdir(args.proto_home):
    print('{0} is not a directory.'.format(args.proto_home))
    sys.exit(1)

if not os.path.isfile(args.test_driver):
    print('{0} is not a file.'.format(args.test_driver))
    sys.exit(1)
if not os.access(args.test_driver, os.X_OK):
    print('{0} is not executable.'.format(args.test_driver))
    sys.exit(1)

tests = args.tests if args.tests else []
if 0 == len(tests):
    # Find all the tests for the protocol.
    for root, dirs, files in os.walk(args.proto_home):
        for file in files:
            absolute_path = os.path.join(root, file)
            if os.path.splitext(absolute_path)[1] == '.json':
                if os.path.isfile(os.path.splitext(absolute_path)[0] + '.bin'):
                    tests.append(os.path.splitext(os.path.relpath(absolute_path, args.proto_home))[0])

# Determine the length of the longest test name.
max = 0
for test in tests:
    if max < len(test):
        max = len(test)

# Execute each test individually.
first = True
for test in tests:
    if first:
        first = False
    else:
        print('')
    print('Running {0}...'.format(test))

    failed = False

    golden_bin_file = os.path.join(args.proto_home, test) + '.bin'
    golden_json_file = os.path.join(args.proto_home, test) + '.json'

    # Put sub-directories' output in a matching tree.
    sub_directory = os.path.join(os.getcwd(), os.path.dirname(test))
    if sub_directory and not os.path.exists(sub_directory):
        os.makedirs(sub_directory)
    actual_bin_file = os.path.join(os.getcwd(), test) + '.bin'
    actual_json_file = os.path.join(os.getcwd(), test) + '.json'

    # Test the binary file.
    subprocess.call(args.test_driver + ' ' + golden_json_file + ' ' + actual_bin_file, shell=True)
    if os.path.exists(actual_bin_file):
        golden_contents = file_to_hex_string(golden_bin_file)
        actual_contents = file_to_hex_string(actual_bin_file)
        seq = difflib.SequenceMatcher(None, golden_contents, actual_contents)
        matches = seq.get_matching_blocks()
        if 2 < len(matches):
            failed = True
            print('--- {0}'.format(golden_bin_file))
            print('+++ {0}'.format(actual_bin_file))
            # print('golden="{0}"'.format(golden_contents))
            # print('actual="{0}"'.format(actual_contents))
        golden_pos = 0
        actual_pos = 0
        curr = 0
        while curr < len(matches):
            golden_idx, golden_len, actual_idx, actual_len = enforce_byte_boundaries(matches[curr][0], matches[curr][1], matches[curr][2])

            if golden_pos < golden_idx:
                print('@@ {0},{1} @@'.format(golden_pos, golden_idx - golden_pos))
                print('+' + golden_contents[golden_pos : golden_idx])
            golden_pos = golden_idx + golden_len

            if actual_pos < actual_idx:
                print('@@ {0},{1} @@'.format(actual_pos, actual_idx - actual_pos))
                print('-' + actual_contents[actual_pos : actual_idx])
            actual_pos = actual_idx + actual_len

            curr += 1

    # Test the JSON file.
    subprocess.call(args.test_driver + ' ' + golden_bin_file + ' ' + actual_json_file, shell=True)
    if os.path.exists(actual_json_file):
        diffs = difflib.unified_diff([line.rstrip('\n') for line in open(golden_json_file)],
                                      [line.rstrip('\n') for line in open(actual_json_file)],
                                      fromfile=golden_json_file,
                                      tofile=actual_json_file,
                                      lineterm='',
                                      n=0)
        for diff in diffs:
            failed = True
            print diff

    print('{0}: {1}'.format(test.rjust(max), 'FAIL' if failed else 'PASS'))
