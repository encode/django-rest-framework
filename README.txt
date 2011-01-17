# To install django-rest-framework...
#
# Requirements:
#   python2.6
#   virtualenv

hg clone https://tomchristie@bitbucket.org/tomchristie/django-rest-framework
cd django-rest-framework/
virtualenv --no-site-packages --distribute --python=python2.6 env
source ./env/bin/activate
pip install -r ./requirements.txt
python ./src/manage.py test

# To build the documentation...

sphinx-build -c docs -b html -d cache docs html

