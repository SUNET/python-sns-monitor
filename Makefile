SOURCE=	src
PIPCOMPILE=pip-compile -v --upgrade --generate-hashes --index-url https://pypi.sunet.se/simple

test:
	pytest --log-cli-level DEBUG

reformat:
	isort --line-width 120 --atomic --project sns_monitor $(SOURCE)
	black --line-length 120 --target-version py37 --skip-string-normalization $(SOURCE)

typecheck:
	mypy --ignore-missing-imports $(SOURCE)

update_deps: requirements.txt $(patsubst %_requirements.in,%_requirements.txt,$(wildcard *_requirements.in))

requirements.txt: requirements.in
	CUSTOM_COMPILE_COMMAND="make update_deps" $(PIPCOMPILE) requirements.in

%_requirements.txt: %_requirements.in
	CUSTOM_COMPILE_COMMAND="make update_deps" $(PIPCOMPILE) $<
