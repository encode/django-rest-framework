#!/usr/bin/env python
import os
import sys
import re
import yaml


def parse_section_content(content):
    """
    Example: given

        [{'Quickstart': 'tutorial/quickstart.md'},
         {'1 - Serialization': 'tutorial/1-serialization.md'},
         ...
        ]

    returns:

        'tutorial', [
            {'name': 'Quickstart', 'mdfile': 'quickstart.md', },
            {'name': '1 - Serialization', 'mdfile': '1-serialization.md', },
            ...
        ]
    """

    folder = ''
    subsections = []
    for row in content:
        name, path = list(row.items())[0]
        tokens = os.path.split(path)
        if not folder:
            folder = tokens[0]
        mdfile  = tokens[-1]
        subsections.append({
            'name': name,
            'mdfile': mdfile,
        })

    return folder, subsections


def run_pandoc(target_folder, title_filename, section, format):
    """
        Example:

        $ cd docs/tutorial
        $ pandoc -o ../../export_docs/tutorial.epub ../../export_docs/title.txt \
            quickstart.md \
            1-serialization.md \
            2-requests-and-responses.md \
            3-class-based-views.md \
            4-authentication-and-permissions.md \
            5-relationships-and-hyperlinked-apis.md \
            6-viewsets-and-routers.md \
            7-schemas-and-client-libraries.md
    """

    # Build command
    target_file = os.path.join(target_folder, "%s.%s" % (section.get('folder'), format))
    command = "pandoc -o %s %s " % (target_file, title_filename)
    items = [item.get('mdfile') for item in section.get('subsections')]
    command += ' '.join(items)

    # Execute
    print('\x1b[1;33;40m Building: "%s" \x1b[0m' % target_file)
    print(">>> " + command)
    os.system(command)


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def help():
    print("""
- Exports DRF docs in different formats
- Requires "pandoc"
- Check pandoc documentation for a complete list of available formats

Please specify one or more formats on command line;
example:

    $ %s epub docx
""" % sys.argv[0])


def main():

    # Retrieve required formats from command line
    formats = sys.argv[1:]
    if len(formats) <= 0:
        help()
        return

    # Parse mkdocs.yml
    with open("mkdocs.yml", 'r') as stream:
        config = yaml.safe_load(stream)
        site_name = config.get('site_name')
        pages = config.get('pages')

    # Parse pages
    sections = []
    for page in pages:
        title, content = list(page.items())[0]
        if isinstance(content, list):
            folder, subsections = parse_section_content(content)
            sections.append({
                'title': title,
                'folder': folder,
                'subsections': subsections,
            })

    # Create destination folder
    target_folder = os.path.abspath(os.path.join('.', 'export_docs'))
    if not os.path.exists(target_folder):
        os.mkdir(target_folder)
    title_filename = os.path.join(target_folder, 'title.txt')
    version = get_version('rest_framework')

    # Loop on sections
    starting_directory = os.getcwd()
    for section in sections:
        try:

            # Build title file
            with open(title_filename, 'w') as title_file:
                title_file.write(
                    '---\ntitle: %s %s - %s\nlanguage: en-US\n...\n' % (
                        site_name,
                        version,
                        section.get('title')
                    )
                )

            # Run pandoc
            os.chdir(os.path.join('docs', section.get('folder')))
            for format in formats:
                run_pandoc(target_folder, title_filename, section, format)

        except Exception as e:
            print('[ERROR] ' + str(e))

        finally:
            os.chdir(starting_directory)

    # cleanup
    os.remove(title_filename)


if __name__ == "__main__":
    main()
