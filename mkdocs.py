#!/usr/bin/env python

import markdown
import os
import re
import shutil
import sys

root_dir = os.path.dirname(__file__)
docs_dir = os.path.join(root_dir, 'docs')
html_dir = os.path.join(root_dir, 'html')

local = not '--deploy' in sys.argv

if local:
    base_url = 'file://%s/' % os.path.normpath(os.path.join(os.getcwd(), html_dir))
    suffix = '.html'
    index = 'index.html'
else:
    base_url = 'http://tomchristie.github.com/django-rest-framework'
    suffix = ''
    index = ''


main_header = '<li class="main"><a href="#{{ anchor }}">{{ title }}</a></li>'
sub_header = '<li><a href="#{{ anchor }}">{{ title }}</a></li>'
code_label = r'<a class="github" href="https://github.com/tomchristie/django-rest-framework/blob/restframework2/djangorestframework/\1"><span class="label label-info">\1</span></a>'

page = open(os.path.join(docs_dir, 'template.html'), 'r').read()

# Copy static files
for static in ['css', 'js', 'img']:
    source = os.path.join(docs_dir, 'static', static)
    target = os.path.join(html_dir, static)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(source, target)

for (dirpath, dirnames, filenames) in os.walk(docs_dir):
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

        build_dir = os.path.join(html_dir, dirpath.lstrip(docs_dir))
        build_file = os.path.join(build_dir, filename[:-3] + '.html')

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        output = page.replace('{{ content }}', content).replace('{{ toc }}', toc).replace('{{ base_url }}', base_url).replace('{{ suffix }}', suffix).replace('{{ index }}', index)
        output = output.replace('{{ page_id }}', filename[:-3])
        output = re.sub(r'a href="([^"]*)\.md"', r'a href="\1%s"' % suffix, output)
        output = re.sub(r'<pre><code>:::bash', r'<pre class="prettyprint lang-bsh">', output)
        output = re.sub(r'<pre>', r'<pre class="prettyprint lang-py">', output)
        output = re.sub(r'<a class="github" href="([^"]*)"></a>', code_label, output)
        open(build_file, 'w').write(output.encode('utf-8'))
