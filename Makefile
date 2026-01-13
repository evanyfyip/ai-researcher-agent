.PHONY: pulse tests regen open-latest

pulse:
	uv run python -m src.pulse
	echo "Pulse report successfully generated."
	echo "You can view it by running the 'make open-latest' in the terminal."

tests:
	uv run python -m unittest discover -s tests

regen:
	uv run python -m src.pulse --from-json $(SUBDIR)

open-latest:
	open "$$(ls -dt output/generated_at_* | head -n 1)/pulse_report.html"
