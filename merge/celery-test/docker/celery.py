#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import importlib
import os
import re
import sys
from pathlib import Path

from celery.__main__ import main

MODULE_NAME = os.environ.get("MODULE_NAME", "celery_test")
MODULE = importlib.import_module(MODULE_NAME, package=None)
MODULE_PATH = Path(MODULE.__file__).parent

if __name__ == '__main__':
    # Change the current working directory to the module's path
    os.chdir(MODULE_PATH)

    # remove the script extension from sys.argv[0]
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # Insert the module name into sys.argv to set the app
    sys.argv.insert(1, f"--app={MODULE_NAME}")

    # run the Celery main function
    sys.exit(main())
