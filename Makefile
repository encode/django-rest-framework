.PHONY: clean install docs tests all

clean:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete
	rm -rf ./site
	rm -rf ./htmlcov
	rm -rf ./coverage
	rm -rf ./build
	rm -rf ./dist

install:
	pip install django
	pip install -r requirements.txt

docs:
	mkdocs build

tests:
	python runtests.py

all: clean install docs tests
