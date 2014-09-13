#!/usr/bin/env python

import markdown
import os
import re
import shutil
import sys

root_dir = os.path.abspath(os.path.dirname(__file__))
docs_dir = os.path.join(root_dir, 'docs')
html_dir = os.path.join(root_dir, 'html')

local = not '--deploy' in sys.argv
preview = '-p' in sys.argv

if local:
    base_url = 'file://%s/' % os.path.normpath(os.path.join(os.getcwd(), html_dir))
    suffix = '.html'
    index = 'index.html'
else:
    base_url = 'http://www.django-rest-framework.org'
    suffix = ''
    index = ''


main_header = '<li class="main"><a href="#{{ anchor }}">{{ title }}</a></li>'
sub_header = '<li><a href="#{{ anchor }}">{{ title }}</a></li>'
code_label = r'<a class="github" href="https://github.com/tomchristie/django-rest-framework/tree/master/rest_framework/\1"><span class="label label-info">\1</span></a>'

page = open(os.path.join(docs_dir, 'template.html'), 'r').read()

# Copy static files
# for static in ['css', 'js', 'img']:
#     source = os.path.join(docs_dir, 'static', static)
#     target = os.path.join(html_dir, static)
#     if os.path.exists(target):
#         shutil.rmtree(target)
#     shutil.copytree(source, target)


# Hacky, but what the hell, it'll do the job
path_list = [
    'index.md',
    'tutorial/quickstart.md',
    'tutorial/1-serialization.md',
    'tutorial/2-requests-and-responses.md',
    'tutorial/3-class-based-views.md',
    'tutorial/4-authentication-and-permissions.md',
    'tutorial/5-relationships-and-hyperlinked-apis.md',
    'tutorial/6-viewsets-and-routers.md',
    'api-guide/requests.md',
    'api-guide/responses.md',
    'api-guide/views.md',
    'api-guide/generic-views.md',
    'api-guide/viewsets.md',
    'api-guide/routers.md',
    'api-guide/parsers.md',
    'api-guide/renderers.md',
    'api-guide/serializers.md',
    'api-guide/fields.md',
    'api-guide/relations.md',
    'api-guide/authentication.md',
    'api-guide/permissions.md',
    'api-guide/throttling.md',
    'api-guide/filtering.md',
    'api-guide/pagination.md',
    'api-guide/content-negotiation.md',
    'api-guide/format-suffixes.md',
    'api-guide/reverse.md',
    'api-guide/exceptions.md',
    'api-guide/status-codes.md',
    'api-guide/testing.md',
    'api-guide/settings.md',
    'topics/documenting-your-api.md',
    'topics/ajax-csrf-cors.md',
    'topics/browser-enhancements.md',
    'topics/browsable-api.md',
    'topics/rest-hypermedia-hateoas.md',
    'topics/third-party-resources.md',
    'topics/contributing.md',
    'topics/rest-framework-2-announcement.md',
    'topics/2.2-announcement.md',
    'topics/2.3-announcement.md',
    'topics/2.4-announcement.md',
    'topics/release-notes.md',
    'topics/credits.md',
]

prev_url_map = {}
next_url_map = {}
for idx in range(len(path_list)):
    path = path_list[idx]
    rel = '../' * path.count('/')

    if idx == 1 and not local:
        # Link back to '/', not '/index'
        prev_url_map[path] = '/'
    elif idx > 0:
        prev_url_map[path] = rel + path_list[idx - 1][:-3] + suffix

    if idx < len(path_list) - 1:
        next_url_map[path] = rel + path_list[idx + 1][:-3] + suffix


for (dirpath, dirnames, filenames) in os.walk(docs_dir):
    relative_dir = dirpath.replace(docs_dir, '').lstrip(os.path.sep)
    build_dir = os.path.join(html_dir, relative_dir)

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    for filename in filenames:
        path = os.path.join(dirpath, filename)
        relative_path = os.path.join(relative_dir, filename)

        if not filename.endswith('.md'):
            if relative_dir:
                output_path = os.path.join(build_dir, filename)
                shutil.copy(path, output_path)
            continue

        output_path = os.path.join(build_dir, filename[:-3] + '.html')

        toc = ''
        text = open(path, 'r').read().decode('utf-8')
        main_title = None
        description = 'Django, API, REST'
        for line in text.splitlines():
            if line.startswith('# '):
                title = line[2:].strip()
                template = main_header
                description = description + ', ' + title
            elif line.startswith('## '):
                title = line[3:].strip()
                template = sub_header
            else:
                continue

            if not main_title:
                main_title = title
            anchor = title.lower().replace(' ', '-').replace(':-', '-').replace("'", '').replace('?', '').replace('.', '')
            template = template.replace('{{ title }}', title)
            template = template.replace('{{ anchor }}', anchor)
            toc += template + '\n'

        if filename == 'index.md':
            main_title = 'Django REST framework - Web APIs for Django'
        else:
            main_title = main_title + ' - Django REST framework'

        if relative_path == 'index.md':
            canonical_url = base_url
        else:
            canonical_url = base_url + '/' + relative_path[:-3] + suffix
        prev_url = prev_url_map.get(relative_path)
        next_url = next_url_map.get(relative_path)

        content = markdown.markdown(text, ['headerid'])

        output = page.replace('{{ content }}', content).replace('{{ toc }}', toc).replace('{{ base_url }}', base_url).replace('{{ suffix }}', suffix).replace('{{ index }}', index)
        output = output.replace('{{ title }}', main_title)
        output = output.replace('{{ description }}', description)
        output = output.replace('{{ page_id }}', filename[:-3])
        output = output.replace('{{ canonical_url }}', canonical_url)

        if filename =='index.md':
            output = output.replace('{{ ad_block }}', """<hr/>
              <script type="text/javascript" src="//cdn.fusionads.net/fusion.js?zoneid=1332&serve=C6SDP2Y&placement=djangorestframework" id="_fusionads_js"></script>""")
        else:
            output = output.replace('{{ ad_block }}', '')

        if prev_url:
            output = output.replace('{{ prev_url }}', prev_url)
            output = output.replace('{{ prev_url_disabled }}', '')
        else:
            output = output.replace('{{ prev_url }}', '#')
            output = output.replace('{{ prev_url_disabled }}', 'disabled')

        if next_url:
            output = output.replace('{{ next_url }}', next_url)
            output = output.replace('{{ next_url_disabled }}', '')
        else:
            output = output.replace('{{ next_url }}', '#')
            output = output.replace('{{ next_url_disabled }}', 'disabled')

        output = re.sub(r'a href="([^"]*)\.md"', r'a href="\1%s"' % suffix, output)
        output = re.sub(r'<pre><code>:::bash', r'<pre class="prettyprint lang-bsh">', output)
        output = re.sub(r'<pre>', r'<pre class="prettyprint lang-py">', output)
        output = re.sub(r'<a class="github" href="([^"]*)"></a>', code_label, output)
        open(output_path, 'w').write(output.encode('utf-8'))

if preview:
    import subprocess

    url = 'html/index.html'

    try:
        subprocess.Popen(["open", url])  # Mac
    except OSError:
        subprocess.Popen(["xdg-open", url])  # Linux
    except:
        os.startfile(url)  # Windows
