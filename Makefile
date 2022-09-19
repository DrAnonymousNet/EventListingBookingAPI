.PHONY: all help translate test clean update compass collect rebuild

SETTINGS={{ Event }}.settings

# target: all - Default target. Does nothing.
all:
	@echo "Hello $(LOGNAME), nothing to do by default"
	@echo "Try 'make help'"

# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

# target: translate - calls the "makemessages" django command
translate:
	cd {{ project_name }} && django-admin.py makemessages --settings=$(SETTINGS) -i "site-static/*" -a --no-location

# target: test - calls the "test" django command
test:
	django-admin.py test --settings=$(TEST_SETTINGS)

# target: clean - remove all ".pyc" files
clean:
	django-admin.py clean_pyc --settings=$(SETTINGS)

# target: update - install (and update) pip requirements
update:
	pip install -U -r requirements.pip


# target: collect - calls the "collectstatic" django command
collect:
	django-admin.py collectstatic --settings=$(SETTINGS) --noinput

# target: rebuild - clean, update, compass, collect, then rebuild all data
rebuild: clean update compass collect
	django-admin.py reset_db --settings=$(SETTINGS) --router=default --noinput
	django-admin.py syncdb --settings=$(SETTINGS) --noinput
	django-admin.py migrate --settings=$(SETTINGS)
	#django-admin.py loaddata --settings=$(SETTINGS) <your fixtures here>

ipy:
	python manage.py shell_plus $(RUN_ARGS)

server:
	python manage.py runserver ${RUN_ARGS}

# target: run - run the server
run:
	python manage.py runserver_plus $(RUN_ARGS)

# target: migrations - generate migrations
migrations:
	python manage.py makemigrations $(RUN_ARGS)

migrate:
	python manage.py migrate $(RUN_ARGS)
