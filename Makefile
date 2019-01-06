.PHONY : all test watch

all : venv

test : all
	venv/bin/python -m pytest pingdom_alert/[a-z]*.py

watch : all
	ls pingdom_alert/*.py | entr -cr make -s test

venv : requirements.txt
	python3 -m venv $@
	venv/bin/pip install -U -r $<
	touch $@
