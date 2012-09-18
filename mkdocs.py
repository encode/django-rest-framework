#!/usr/bin/env python


#### Requirements
#
# Markdown and Yaml installed
# pip install markdown
# pip install PyYAML
#
#
# A YAML config file created
#
#
#

#### terminal usage
# python mkdocs.py [options]
# options:
#   -c --configfile "Config file"


import markdown
import os
import re
import shutil
import sys
from optparse import OptionParser
import yaml


parser = OptionParser()
parser.add_option("-c", "--configfile", type="string", action="store", dest="conf_file_path", help="Config File Path (YAML format)")

(options, args) = parser.parse_args()

def create_files(conf_file_path):
    # read the conf file
    with open(conf_file_path, 'r') as f:
        conf = yaml.load(f)

    root_dir = os.path.dirname(__file__)
    docs_dir = os.path.join(root_dir, conf['docs_dir'])  # where it gets the MD files from
    html_dir = os.path.join(root_dir, conf['html_dir'])  # where it puts 'em'

    #get the title
    project_title = conf['project_title']

    # is this a local build?
    local = not '--deploy' in sys.argv  # If not --deploy all links end with .html and base links contain file

    if local:
        base_url = 'file://%s/' % os.path.normpath(os.path.join(os.getcwd(), html_dir))
        suffix = '.html'
        index = 'index.html'
    else:
        base_url = conf['base_url']  # if for deployment use actual docs URL.. maybe make all relative later
        suffix = ''  # .html only needed for local
        index = ''

    main_header = '<li class="main"><a href="#{{ anchor }}">{{ title }}</a></li>'
    sub_header = '<li><a href="#{{ anchor }}">{{ title }}</a></li>'
    code_label = r'<a class="github" href="https://github.com/tomchristie/django-rest-framework/blob/restframework2/djangorestframework/\1"><span class="label label-info">\1</span></a>'

    new_page = open(os.path.join(docs_dir, 'template.html'), 'r').read()

    # copy static
    for static in conf['static_dirs']:
        source = os.path.join(root_dir, static['source'])
        target = os.path.join(html_dir, static['target'])
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target)

    # ========================================================================================================================

    # create the naivgation based on the YAML settings
    navigation = "<ul>{{ content }}</ul>"

    nav_content = ""

    for section in conf['nav']:

        # does this section have sub pages?
        if 'pages' not in section:
            # output non drop down nav
            top_nav = "<li><a href='" + base_url + section['file'][:-3] + suffix + "' >" + section['title'] + "</a></li>"
        else:
            # output drop down nav
            top_nav = "<li>" + section['title'] + " <ul>{{ drop_down }}</ul></li>"

            drop_down = ""
            for page in section['pages']:
                inner_nav = "<li><a href='" + base_url + page['file'][:-3] + suffix + "' >" + page['title'] + "</a></li>"
                drop_down += inner_nav
            top_nav = top_nav.replace("{{ drop_down }}", drop_down)

        nav_content += top_nav

    navigation = navigation.replace("{{ content }}", nav_content)

    # ========================================================================================================================

    # loop through all MD files
    #for (dirpath, dirnames, filenames) in os.walk(docs_dir):  # go through everything

    #    for filename in filenames:
    #        if not filename.endswith('.md'):  # ignore non md files
    #            continue

    def convert_file(filepath):
         # build the tabe of contents

         # ========================================================================================================================

        if not os.path.dirname(filepath):
            #print 'is file'
            dirpath = docs_dir
        else:
            #print os.path.dirname(filepath)
            dirpath = os.path.join(docs_dir, os.path.dirname(filepath))

        filename = os.path.basename(filepath)

        # ========================================================================================================================

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

        content = markdown.markdown(text, ['headerid'])  # generate the markdown content

        # ========================================================================================================================
        build_dir = os.path.join(html_dir, dirpath.lstrip(docs_dir))
        # ive added this if statement as the above command doesnt seem to be working correctly ====================================
        if dirpath != docs_dir:
            build_path = dirpath.lstrip(docs_dir)
            build_dir = html_dir + build_path
        # ========================================================================================================================

        build_file = os.path.join(build_dir, filename[:-3] + '.html')

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        output = new_page.replace('{{ content }}', content).replace('{{ toc }}', toc).replace('{{ base_url }}', base_url).replace('{{ suffix }}', suffix).replace('{{ index }}', index)

        #add project title
        output = output.replace('{{ project_title }}', project_title).replace('{{ version_number }}', conf['version_number']).replace('{{ navigation }}', navigation)

        output = output.replace('{{ page_id }}', filename[:-3])
        output = re.sub(r'a href="([^"]*)\.md"', r'a href="\1%s"' % suffix, output)  # Go through all links and remove MD suffixes
        output = re.sub(r'<pre><code>:::bash', r'<pre class="prettyprint lang-bsh">', output)  # next two lines about adding in pretty print code highlights
        output = re.sub(r'<pre>', r'<pre class="prettyprint lang-py">', output)
        output = re.sub(r'<a class="github" href="([^"]*)"></a>', code_label, output)

        open(build_file, 'w').write(output.encode('utf-8'))

    # ========================================================================================================================

    #loop through and convert files
    for section in conf['nav']:
        # does this section have sub pages?
        if 'pages' not in section:
            convert_file(section['file'])
        else:
            for page in section['pages']:
                convert_file(page['file'])



# output messages if options are missing
if not options.conf_file_path:
    print '\tYou did not specifiy a YAML source config file. Do this using -c or --configfile'
else:
    if  os.path.splitext(options.conf_file_path)[1] == '.yaml':  # get the file type
        create_files(options.conf_file_path)
    else:
        print '\tYou did not specifiy a YAML source config file.'
