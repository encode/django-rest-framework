# Contributing to REST framework

> The world can only really be changed one piece at a time. The art is picking that piece.
>
> &mdash; [Tim Berners-Lee][cite]

## Get the source

Use `git` to clone the master REST Framework source files to your local systme. If you plan to contribute, 
to the project, you also need to fork the repo on github. See https://help.github.com/articles/fork-a-repo 
for more information.

## Running the tests

Ensure your PYTHONPATH is configured so that the copy of REST Framework from your local git repo is picked up, 
not any other version you may have installed on your system.

Then, invoked the `runtests/runtests.py` script to execute all unittests.

Here is an example session:

```
/home/mydir/django-rest-framework$ export PYTHONPATH=/home/mydir/djangorestramework:$PYTHONPATH
/home/mydir/django-rest-framework$ rest_framework/runtests/runtests.py
```

## Building the docs

## Managing compatibility issues

**Describe compat module**

[cite]: http://www.w3.org/People/Berners-Lee/FAQ.html