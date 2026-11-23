.PHONY: run install clean

run:
	uv run streamlit run app.py

install:
	uv sync

clean:
	rm -rf .venv __pycache__ .streamlit
