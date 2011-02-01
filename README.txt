# To install django-rest-framework in a virtualenv environment...

hg clone https://tomchristie@bitbucket.org/tomchristie/django-rest-framework
cd django-rest-framework/
virtualenv --no-site-packages --distribute --python=python2.6 env
source ./env/bin/activate
pip install -r requirements.txt

# To build the documentation...

pip install -r docs/requirements.txt
sphinx-build -c docs -b html -d docs/build docs html

# To run the examples...

pip install -r examples/requirements.txt
cd examples
export PYTHONPATH=..
python manage.py syncdb
python manage.py runserver

