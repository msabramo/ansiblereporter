
Ansible command output parsers
==============================

This module contains scripts to run ansible commands on targets and storing
the results to nicely formatted output files. You can either use the default
scripts included, or use the module to process output data as required.

Major difference to normal ansible is that all results are collected before 
reporting, avoiding issues with mixed asynchronous output from various hosts
when using multiple forks.

Installing
==========

Run one of following to install these tools:

    make install
    PREFIX=/usr/local make install

Included commands
=================

./bin/ansible-reporter
  Run single ansible command with options to output data to files, either with
  default formatter or as json formatted results. With no options results are
  collected and reported to stdout in mostly ansible compatible text output.

./bin/ansible-playbook-reporter
  Run ansible playbook with similar options to output data from playbook steps
  to files as ansible-reporter. The output differs from playbook output, because
  for each host output from each ansible playbook task is reported fully.

Example data parsers
====================

Trivial example data parsers are available in examples/ directory of source
code tree.

