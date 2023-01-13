.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))
MAKEFLAGS := --jobs=999

update-schema:
	cd backend && poetry run ./manage.py export_schema --path schema.gql api.schema

run-balancer:
	@echo "----- START BALANCER-----\n\n"
	haproxy -f .haproxy.cfg

run-web:
	@echo "----- START FRONT-----\n\n"
	cd frontend && yarn run web-dev

run-back:
	@echo "----- START BACK -----\n\n"
	$(if $(TEST_DB),$(MAKE) db-reset)
	cd backend && poetry run ./manage.py runserver 0.0.0.0:8080

run-local: run-balancer run-back run-web

run-test: export DJANGO_CONFIGURATION = Tests
run-test: export TEST_DB = /tmp/listmanager-test-db.sqlite3
run-test: run-back

db-migrate:
	cd backend && poetry run ./manage.py migrate

db-reset: TEST_DB := $(if $(TEST_DB),$(TEST_DB),backend/db.sqlite3)
db-reset:
	rm -rf ${TEST_DB}
	cd backend && poetry run ./manage.py migrate
	$(MAKE) db-migrate