SOURCE=	src
EDUIDCOMMON= ../eduid-common/src

test:
	pytest --log-cli-level DEBUG

reformat:
	isort --line-width 120 --atomic --project sns_monitor $(SOURCE)
	black --line-length 120 --target-version py37 --skip-string-normalization $(SOURCE)

typecheck:
	mypy --ignore-missing-imports $(SOURCE)

typecheck_extra:
	mypy --ignore-missing-imports $(EDUIDCOMMON) $(SOURCE)

