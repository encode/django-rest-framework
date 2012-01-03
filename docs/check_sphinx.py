import pytest
import subprocess

def test_build_docs(tmpdir):
    doctrees = tmpdir.join("doctrees")
    htmldir = "html" #we want to keep the docs
    subprocess.check_call([
        "sphinx-build", "-q", "-bhtml",
          "-d", str(doctrees), ".", str(htmldir)])
