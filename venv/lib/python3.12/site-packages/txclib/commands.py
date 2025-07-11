# -*- coding: utf-8 -*-
"""In this file we have all the top level commands for the transifex client.
Since we're using a way to automatically list them and execute them, when
adding code to this file you must take care of the following:
 * Added functions must begin with 'cmd_' followed by the actual name of the
   command being used in the command line (eg cmd_init)
 * The description for each function that we display to the user is read from
   the func_doc attribute which reads the doc string. So, when adding
   docstring to a new function make sure you add an oneliner which is
   descriptive and is meant to be seen by the user.
 * When including libraries, it's best if you include modules instead of
   functions because that way our function resolution will work faster and the
   chances of overlapping are minimal
 * All functions should use the OptionParser and should have a usage and
   descripition field.
"""
import os
import re
import shutil
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from six.moves import input

from txclib import utils, project
from txclib.config import OrderedRawConfigParser
from txclib.exceptions import UnInitializedError
from txclib.parsers import delete_parser, help_parser, parse_csv_option, \
    status_parser, pull_parser, set_parser, push_parser, init_parser
from txclib.paths import posix_path
from txclib.log import logger


def cmd_init(argv, path_to_tx):
    """Initialize a new transifex project."""
    parser = init_parser()
    (options, args) = parser.parse_args(argv)
    if len(args) > 1:
        parser.error("Too many arguments were provided. Aborting...")
    if args:
        path_to_tx = args[0]
    else:
        path_to_tx = os.getcwd()

    save = options.save
    # if we already have a config file and we are not told to override it
    # in the args we have to ask
    if os.path.isdir(os.path.join(path_to_tx, ".tx")) and not save:
        logger.info("There is already a tx folder!")
        if not utils.confirm(
            prompt='Do you want to delete it and reinit the project?',
            default=False
        ):
            return
        # Clean the old settings
        # FIXME: take a backup
        else:
            save = True
            rm_dir = os.path.join(path_to_tx, ".tx")
            shutil.rmtree(rm_dir)

    logger.info("Creating .tx folder...")
    os.mkdir(os.path.join(path_to_tx, ".tx"))

    default_transifex = "https://www.transifex.com"
    transifex_host = options.host or input("Transifex instance [%s]: " %
                                           default_transifex)

    if not transifex_host:
        transifex_host = default_transifex
    if not transifex_host.startswith(('http://', 'https://')):
        transifex_host = 'https://' + transifex_host

    config_file = os.path.join(path_to_tx, ".tx", "config")
    if not os.path.exists(config_file):
        # The path to the config file (.tx/config)
        logger.info("Creating skeleton...")
        # Handle the credentials through transifexrc
        config = OrderedRawConfigParser()
        config.add_section('main')
        config.set('main', 'host', transifex_host)
        # Touch the file if it doesn't exist
        logger.info("Creating config file...")
        fh = open(config_file, 'w')
        config.write(fh)
        fh.close()

    prj = project.Project(path_to_tx)
    prj.getset_host_credentials(transifex_host, username=options.user,
                                password=options.password,
                                token=options.token, save=save)
    prj.save()
    logger.info("Done.")


def cmd_set(argv, path_to_tx):
    """Add local or remote files under transifex"""
    parser = set_parser()
    (options, args) = parser.parse_args(argv)

    # Implement options/args checks
    # TODO !!!!!!!
    if options.local:
        try:
            expression = args[0]
        except IndexError:
            parser.error("Please specify an expression.")
        if not options.resource:
            parser.error("Please specify a resource")
        if not options.source_language:
            parser.error("Please specify a source language.")
        if '<lang>' not in expression:
            parser.error("The expression you have provided is not valid.")
        if not utils.valid_slug(options.resource):
            parser.error("Invalid resource slug. The format is <project_slug>"
                         ".<resource_slug> and the valid characters include"
                         " [_-\w].")
        _auto_local(path_to_tx, options.resource,
                    source_language=options.source_language,
                    expression=expression, source_file=options.source_file,
                    execute=options.execute, regex=False)
        if options.execute:
            _set_minimum_perc(options.resource, options.minimum_perc,
                              path_to_tx)
            _set_mode(options.resource, options.mode, path_to_tx)
            _set_type(options.resource, options.i18n_type, path_to_tx)
        return

    if options.remote:
        try:
            url = args[0]
        except IndexError:
            parser.error("Please specify an remote url")
        _auto_remote(path_to_tx, url)
        _set_minimum_perc(options.resource, options.minimum_perc, path_to_tx)
        _set_mode(options.resource, options.mode, path_to_tx)
        return

    if options.is_source:
        resource = options.resource
        if not resource:
            parser.error("You must specify a resource name with the "
                         "-r|--resource flag.")

        lang = options.language
        if not lang:
            parser.error("Please specify a source language.")

        if len(args) != 1:
            parser.error("Please specify a file.")

        if not utils.valid_slug(resource):
            parser.error("Invalid resource slug. The format is <project_slug>"
                         ".<resource_slug> and the valid characters include "
                         "[_-\w].")

        file = args[0]
        # Calculate relative path
        path_to_file = os.path.relpath(file, path_to_tx)
        _set_source_file(path_to_tx, resource, options.language, path_to_file)
    elif options.resource or options.language:
        resource = options.resource
        lang = options.language

        if len(args) != 1:
            parser.error("Please specify a file")

        # Calculate relative path
        path_to_file = os.path.relpath(args[0], path_to_tx)

        _go_to_dir(path_to_tx)

        if not utils.valid_slug(resource):
            parser.error("Invalid resource slug. The format is <project_slug>"
                         ".<resource_slug> and the valid characters include "
                         "[_-\w].")
        _set_translation(path_to_tx, resource, lang, path_to_file)

    _set_mode(options.resource, options.mode, path_to_tx)
    _set_type(options.resource, options.i18n_type, path_to_tx)
    _set_minimum_perc(options.resource, options.minimum_perc, path_to_tx)

    logger.info("Done.")
    return


def _auto_local(path_to_tx, resource, source_language, expression,
                execute=False, source_file=None, regex=False):
    """Auto configure local project."""
    # The path everything will be relative to
    curpath = os.path.abspath(os.curdir)

    # Force expr to be a valid regex expr (escaped) but keep <lang> intact
    expr_re = utils.regex_from_filefilter(expression, curpath)
    expr_rec = re.compile(expr_re)

    if not execute:
        logger.info("Only printing the commands which will be run if the "
                    "--execute switch is specified.")

    # First, let's construct a dictionary of all matching files.
    # Note: Only the last matching file of a language will be stored.
    translation_files = {}
    for f_path in utils.files_in_project(curpath):
        match = expr_rec.match(posix_path(f_path))
        if match:
            lang = match.group(1)
            if lang == source_language and not source_file:
                source_file = f_path
            else:
                translation_files[lang] = f_path

    if not source_file:
        raise Exception("Could not find a source language file. Please run "
                        "set --source manually and then re-run this command "
                        "or provide the source file with the -s flag.")
    if execute:
        logger.info("Updating source for resource %s ( %s -> %s )." % (
                    resource, source_language, os.path.relpath(
                        source_file, path_to_tx)
                    ))
        _set_source_file(path_to_tx, resource, source_language,
                         os.path.relpath(source_file, path_to_tx))
    else:
        logger.info('\ntx set --source -r %(res)s -l %(lang)s %(file)s\n' % {
            'res': resource,
            'lang': source_language,
            'file': os.path.relpath(source_file, curpath)})

    prj = project.Project(path_to_tx)

    if execute:
        try:
            prj.config.get("%s" % resource, "source_file")
        except configparser.NoSectionError:
            raise Exception("No resource with slug \"%s\" was found.\nRun "
                            "'tx set --auto-local -r %s \"expression\"' to "
                            "do the initial configuration." % resource)

    # Now let's handle the translation files.
    if execute:
        logger.info("Updating file expression for resource %s ( %s )." % (
                    resource, expression))
        # Eval file_filter relative to root dir
        file_filter = posix_path(
            os.path.relpath(os.path.join(curpath, expression), path_to_tx)
        )
        prj.config.set("%s" % resource, "file_filter", file_filter)
    else:
        for (lang, f_path) in sorted(translation_files.items()):
            logger.info('tx set -r %(res)s -l %(lang)s %(file)s' % {
                'res': resource,
                'lang': lang,
                'file': os.path.relpath(f_path, curpath)})

    if execute:
        prj.save()


def _auto_remote(path_to_tx, url):
    """Initialize a remote project/resource to the current directory."""
    logger.info("Auto configuring local project from remote URL...")

    type, vars = utils.parse_tx_url(url)
    prj = project.Project(path_to_tx)
    username, password = prj.getset_host_credentials(vars['hostname'])

    if type.startswith('project'):
        logger.info("Getting details for project %s" % vars['project'])
        proj_info = utils.get_details(
            'project_details',
            username, password,
            hostname=vars['hostname'],
            project=vars['project'])
        resources = ['.'.join([vars['project'],
                     r['slug']]) for r in proj_info['resources']]
        logger.info("%s resources found. Configuring..." % len(resources))
    elif type == 'release':
        logger.info("Getting details for release %s" % vars['release'])
        rel_info = utils.get_details(
            'release_details',
            username, password,
            hostname=vars['hostname'],
            project=vars['project'],
            release=vars['release'])
        resources = []
        for r in rel_info['resources']:
            if 'project' in r:
                resources.append('.'.join([r['project']['slug'], r['slug']]))
            else:
                resources.append('.'.join([vars['project'], r['slug']]))
        logger.info("%s resources found. Configuring..." % len(resources))
    elif type.startswith('resource'):
        logger.info("Getting details for resource %s" % vars['resource'])
        resources = ['.'.join([vars['project'], vars['resource']])]
    else:
        raise Exception("Url '%s' is not recognized." % url)

    for resource in resources:
        logger.info("Configuring resource %s." % resource)
        proj, res = resource.split('.')
        res_info = utils.get_details(
            'resource_details',
            username, password,
            hostname=vars['hostname'],
            project=proj, resource=res)
        try:
            source_lang = res_info['source_language_code']
            i18n_type = res_info['i18n_type']
        except KeyError:
            raise Exception("Remote server seems to be running an unsupported "
                            "version of Transifex. Either update your server "
                            "software of fallback to a previous version "
                            "of transifex-client.")
        prj.set_remote_resource(
            resource=resource,
            host=vars['hostname'],
            source_lang=source_lang,
            i18n_type=i18n_type)

    prj.save()


def cmd_push(argv, path_to_tx):
    """Push local files to remote server"""
    parser = push_parser()
    (options, args) = parser.parse_args(argv)
    force_creation = options.force_creation
    languages = parse_csv_option(options.languages)
    resources = parse_csv_option(options.resources)
    skip = options.skip_errors
    xliff = options.xliff
    prj = project.Project(path_to_tx)
    if not (options.push_source or options.push_translations):
        parser.error("You need to specify at least one of the -s|--source, "
                     "-t|--translations flags with the push command.")

    prj.push(
        force=force_creation, resources=resources, languages=languages,
        skip=skip, source=options.push_source,
        translations=options.push_translations,
        no_interactive=options.no_interactive,
        xliff=xliff
    )
    logger.info("Done.")


def cmd_pull(argv, path_to_tx):
    """Pull files from remote server to local repository"""
    parser = pull_parser()
    (options, args) = parser.parse_args(argv)
    if options.fetchall and options.languages:
        parser.error("You can't user a language filter along with the "
                     "-a|--all option")
    languages = parse_csv_option(options.languages)
    resources = parse_csv_option(options.resources)
    pseudo = options.pseudo
    # Should we download as xliff?
    xliff = options.xliff
    skip = options.skip_errors
    minimum_perc = options.minimum_perc or None

    _go_to_dir(path_to_tx)

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    prj.pull(
        languages=languages, resources=resources, overwrite=options.overwrite,
        fetchall=options.fetchall, fetchsource=options.fetchsource,
        force=options.force, skip=skip, minimum_perc=minimum_perc,
        mode=options.mode, pseudo=pseudo, xliff=xliff
    )
    logger.info("Done.")


def _set_source_file(path_to_tx, resource, lang, path_to_file):
    """Reusable method to set source file."""
    proj, res = resource.split('.')
    if not proj or not res:
        raise Exception("\"%s.%s\" is not a valid resource identifier. "
                        "It should be in the following format "
                        "project_slug.resource_slug." %
                        (proj, res))
    if not lang:
        raise Exception("You haven't specified a source language.")

    _go_to_dir(path_to_tx)

    if not os.path.exists(path_to_file):
        raise Exception("tx: File ( %s ) does not exist." %
                        os.path.join(path_to_tx, path_to_file))

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    root_dir = os.path.abspath(path_to_tx)

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        raise Exception("File must be under the project root directory.")

    logger.info("Setting source file for resource %s.%s ( %s -> %s )." % (
        proj, res, lang, path_to_file))

    path_to_file = os.path.relpath(path_to_file, root_dir)

    prj = project.Project(path_to_tx)

    # FIXME: Check also if the path to source file already exists.
    try:
        try:
            prj.config.get("%s.%s" % (proj, res), "source_file")
        except configparser.NoSectionError:
            prj.config.add_section("%s.%s" % (proj, res))
        except configparser.NoOptionError:
            pass
    finally:
        prj.config.set(
            "%s.%s" % (proj, res), "source_file", posix_path(path_to_file)
        )
        prj.config.set("%s.%s" % (proj, res), "source_lang", lang)

    prj.save()


def _set_translation(path_to_tx, resource, lang, path_to_file):
    """Reusable method to set translation file."""

    proj, res = resource.split('.')
    if not project or not resource:
        raise Exception("\"%s\" is not a valid resource identifier. "
                        "It should be in the following format "
                        "project_slug.resource_slug." %
                        resource)

    _go_to_dir(path_to_tx)

    # Warn the user if the file doesn't exist
    if not os.path.exists(path_to_file):
        logger.info("Warning: File '%s' doesn't exist." % path_to_file)

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    root_dir = os.path.abspath(path_to_tx)

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        raise Exception("File must be under the project root directory.")

    if lang == prj.config.get("%s.%s" % (proj, res), "source_lang"):
        raise Exception("tx: You cannot set translation file for "
                        "the source language. Source languages contain "
                        "the strings which will be translated!")

    logger.info("Updating translations for resource %s ( %s -> %s )." % (
                resource, lang, path_to_file))
    path_to_file = os.path.relpath(path_to_file, root_dir)
    prj.config.set(
        "%s.%s" % (proj, res), "trans.%s" % lang, posix_path(path_to_file)
    )

    prj.save()


def cmd_status(argv, path_to_tx):
    """Print status of current project"""
    parser = status_parser()
    (options, args) = parser.parse_args(argv)
    resources = parse_csv_option(options.resources)
    prj = project.Project(path_to_tx)
    resources = prj.get_chosen_resources(resources)
    resources_num = len(resources)
    for idx, res in enumerate(resources):
        p, r = res.split('.')
        print("%s -> %s (%s of %s)" % (p, r, idx + 1, resources_num))
        print("Translation Files:")
        slang = prj.get_resource_option(res, 'source_lang')
        sfile = prj.get_resource_option(res, 'source_file') or "N/A"
        lang_map = prj.get_resource_lang_mapping(res)
        print(" - %s: %s (%s)" % (utils.color_text(slang, "RED"),
              sfile, utils.color_text("source", "YELLOW")))
        files = prj.get_resource_files(res)
        fkeys = list(files.keys())
        fkeys.sort()
        for lang in fkeys:
            local_lang = lang
            if lang in list(lang_map.values()):
                local_lang = lang_map.flip[lang]
            print(" - %s: %s" % (utils.color_text(local_lang, "RED"),
                  files[lang]))
        print("")


def cmd_help(argv, path_to_tx):
    """List all available commands"""
    parser = help_parser()
    (options, args) = parser.parse_args(argv)
    if len(args) > 1:
        parser.error("Multiple arguments received. Exiting...")

    # Get all commands
    fns = utils.discover_commands()

    # Print help for specific command
    if len(args) == 1:
        try:
            fns[argv[0]](['--help'], path_to_tx)
        except KeyError:
            utils.logger.error("Command %s not found" % argv[0])
    # or print summary of all commands

    # the code below will only be executed if the KeyError exception is thrown
    # becuase in all other cases the function called with --help will exit
    # instead of return here
    keys = list(fns.keys())
    keys.sort()

    print("Transifex command line client.\n")
    print("Available commands are:")
    for key in keys:
        print("  %-15s\t%s" % (key, getattr(fns[key], '__doc__')))
    print("\nFor more information run %s command --help" % sys.argv[0])


def cmd_delete(argv, path_to_tx):
    """Delete an accessible resource or translation in a remote server."""
    parser = delete_parser()
    (options, args) = parser.parse_args(argv)
    languages = parse_csv_option(options.languages)
    resources = parse_csv_option(options.resources)
    skip = options.skip_errors
    force = options.force_delete
    prj = project.Project(path_to_tx)
    prj.delete(resources, languages, skip, force)
    logger.info("Done.")


def _go_to_dir(path):
    """Change the current working directory to the directory specified as
    argument.

    Args:
        path: The path to chdor to.
    Raises:
        UnInitializedError, in case the directory has not been initialized.
    """
    if path is None:
        raise UnInitializedError(
            "Directory has not been initialized. "
            "Did you forget to run 'tx init' first?"
        )
    os.chdir(path)


def _set_minimum_perc(resource, value, path_to_tx):
    """Set the minimum percentage in the .tx/config file."""
    args = (resource, 'minimum_perc', value, path_to_tx, 'set_min_perc')
    _set_project_option(*args)


def _set_mode(resource, value, path_to_tx):
    """Set the mode in the .tx/config file."""
    args = (resource, 'mode', value, path_to_tx, 'set_default_mode')
    _set_project_option(*args)


def _set_type(resource, value, path_to_tx):
    """Set the i18n type in the .tx/config file."""
    args = (resource, 'type', value, path_to_tx, 'set_i18n_type')
    _set_project_option(*args)


def _set_project_option(resource, name, value, path_to_tx, func_name):
    """Save the option to the project config file."""
    if value is None:
        return
    if not resource:
        logger.debug("Setting the %s for all resources." % name)
        resources = []
    else:
        logger.debug("Setting the %s for resource %s." % (name, resource))
        resources = [resource, ]
    prj = project.Project(path_to_tx)
    getattr(prj, func_name)(resources, value)
    prj.save()
