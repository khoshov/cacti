ENV := export FLASK_APP=app && export FLASK_ENV=development && export FLASK_DEBUG=1

run:
	 ${ENV} && flask run

help:
	 ${ENV} && flask --help

users_create:
	 ${ENV} && flask users_create -a

db_init:
	${ENV} && flask db init

db_migrate:
	${ENV} && flask db migrate

db_upgrade:
	${ENV} && flask db upgrade
