#!/usr/bin/python

import argparse
import difflib
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description='Protocol Input Vs. Output Tester')
parser.add_argument('--pivot_home', default=os.path.dirname(os.path.realpath(__file__)), help='Home of pivot')
parser.add_argument('--proto_home', default=os.path.dirname(os.path.realpath(__file__)), help='Home of protocol')
parser.add_argument('--tests', nargs='+', help='Names of tests to run')
parser.add_argument('test_driver', help='Path to test driver executable')
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
            if os.path.splitext(absolute_path)[1] == '.yaml':
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
    golden_yaml_file = os.path.join(args.proto_home, test) + '.yaml'

    # Put sub-directories' output in a matching tree.
    sub_directory = os.path.join(os.getcwd(), os.path.dirname(test))
    if sub_directory and not os.path.exists(sub_directory):
        os.makedirs(sub_directory)
    actual_bin_file = os.path.join(os.getcwd(), test) + '.bin'
    actual_yaml_file = os.path.join(os.getcwd(), test) + '.yaml'

    # Test the binary file.
    subprocess.call(args.test_driver + ' ' + golden_yaml_file + ' ' + actual_bin_file, shell=True)
    # TODO Convert binary into hexadecimal strings.
    golden_contents = open(golden_bin_file, 'r').read()
    actual_contents = open(actual_bin_file, 'r').read()
    # print('golden="{0}"'.format(golden_contents))
    # print('actual="{0}"'.format(actual_contents))
    seq = difflib.SequenceMatcher(None, golden_contents, actual_contents)
    matches = seq.get_matching_blocks()
    if 2 < len(matches):
        failed = True
        print('--- {0}'.format(golden_bin_file))
        print('+++ {0}'.format(actual_bin_file))
    curr = 0
    while curr < len(matches) - 1:
        i, j, n = matches[curr]
        # print('index={0} i={1} j={2} n={3}'.format(curr, i, j, n))
        if i != j:
            next = curr + 1
            while next < len(matches) - 1 and matches[next][0] != matches[next][1]:
                next += 1
            start = i if i < j else j
            finish = matches[next][0]
            print('@@ {0},{1} @@'.format(start, finish - start))
            print('+' + golden_contents[start : finish])
            print('-' + actual_contents[start : finish])
        curr += 1
    # for i, j, n in matches:
    #     if 0 == n:
    #         break
    #     print('i={0} j={1} n={2}'.format(i, j, n))
    #     if i < j:
    #         print('@@ {0},{1} @@'.format(i, j - i))
    #         print ('+ {0}'.format(actual_contents[i : j]))
    #     elif j < i:
    #         print('@@ {0},{1} @@'.format(j, i - j))
    #         print ('- {0}'.format(golden_contents[j : i]))

    # Test the YAML file.
    subprocess.call(args.test_driver + ' ' + golden_bin_file + ' ' + actual_yaml_file, shell=True)
    diffs = difflib.unified_diff([line.rstrip('\n') for line in open(golden_yaml_file)],
                                  [line.rstrip('\n') for line in open(actual_yaml_file)],
                                  fromfile=golden_yaml_file,
                                  tofile=actual_yaml_file,
                                  lineterm='',
                                  n=0)
    for diff in diffs:
        failed = True
        print diff

    print('{0}: {1}'.format(test.rjust(max), 'FAIL' if failed else 'PASS'))
