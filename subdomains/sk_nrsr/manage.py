#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    _, parl = os.path.dirname(__file__).rsplit('/', 1)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "subdomains.%s.settings" % parl)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)