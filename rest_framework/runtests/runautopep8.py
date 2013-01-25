import codecs
import os
import sys
from autopep8 import fix_file, LineEndingWrapper


class Options(object):
    in_place = True
    ignore = []
    select = []
    max_line_length = 97
    verbose = True
    aggressive = False
    pep8_passes = 100
    diff = False

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


def main(filenames):
    output = codecs.getwriter('utf-8')(sys.stdout.buffer
                                       if sys.version_info[0] >= 3
                                       else sys.stdout)

    output = LineEndingWrapper(output)

    while filenames:
        name = filenames.pop(0)
        if os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in children
                              if f.endswith('.py') and
                              not f.startswith('.')]
                for d in directories:
                    if d.startswith('.'):
                        directories.remove(d)
        else:
            print('[file:%s]' % name)
            try:
                fix_file(name, Options(), output)
            except IOError as error:
                print(str(error))

if __name__ == '__main__':
    filenames = [os.path.join(
        os.path.join(os.path.dirname(__file__), "../.."), './rest_framework/'),
        os.path.join(os.path.join(os.path.dirname(__file__), "../.."), './setup.py')]

    main(filenames)
