#!/bin/bash

venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate ;\
	python -m pip install -Ur requirements.txt
	touch venv/bin/activate
