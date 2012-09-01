#!/usr/bin/env python

import markdown
import os
import re

root = os.path.dirname(__file__)
local = True

if local:
    base_url = 'file://%s/html/' % os.path.normpath(os.path.join(os.getcwd(), root))
    suffix = '.html'
    index = 'index.html'
else:
    base_url = 'http://tomchristie.github.com/restframeworkdocs/'
    suffix = ''
    index = ''


main_header = '<li class="main"><a href="#{{ anchor }}">{{ title }}</a></li>'
sub_header = '<li><a href="#{{ anchor }}">{{ title }}</a></li>'

page = open(os.path.join(root, 'template.html'), 'r').read()

for (dirpath, dirnames, filenames) in os.walk(root):
    for filename in filenames:
        if not filename.endswith('.md'):
            continue

        toc = ''
        text = open(os.path.join(dirpath, filename), 'r').read().decode('utf-8')
        for line in text.splitlines():
            if line.startswith('# '):
                title = line[2:].strip()
                template = main_header
            elif line.startswith('## '):
                title = line[3:].strip()
                template = sub_header
            else:
                continue

            anchor = title.lower().replace(' ', '-').replace(':-', '-').replace("'", '').replace('?', '').replace('.', '')
            template = template.replace('{{ title }}', title)
            template = template.replace('{{ anchor }}', anchor)
            toc += template + '\n'

        content = markdown.markdown(text, ['headerid'])

        build_dir = os.path.join(root, 'html', dirpath)
        build_file = os.path.join(build_dir, filename[:-3] + '.html')

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        output = page.replace('{{ content }}', content).replace('{{ toc }}', toc).replace('{{ base_url }}', base_url).replace('{{ suffix }}', suffix).replace('{{ index }}', index)
        output = re.sub(r'a href="([^"]*)\.md"', r'a href="\1.html"', output)
        open(build_file, 'w').write(output.encode('utf-8'))
