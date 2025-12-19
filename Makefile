.PHONY: pulse tests regen

pulse:
	uv run python -m src.pulse

tests:
	uv run python -m unittest discover -s tests

regen:
	uv run python -m src.pulse --from-json $(SUBDIR)
