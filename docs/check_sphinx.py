import pytest
import subprocess

def test_linkcheck(tmpdir):
    doctrees = tmpdir.join("doctrees")
    htmldir = tmpdir.join("html")
    subprocess.check_call(
        ["sphinx-build", "-q", "-blinkcheck",
          "-d", str(doctrees), ".", str(htmldir)])

def test_build_docs(tmpdir):
    doctrees = tmpdir.join("doctrees")
    htmldir = "html" #we want to keep the docs
    subprocess.check_call([
        "sphinx-build", "-q", "-bhtml",
          "-d", str(doctrees), ".", str(htmldir)])
