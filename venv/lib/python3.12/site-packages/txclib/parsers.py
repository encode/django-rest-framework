# -*- coding: utf-8 -*-

from optparse import OptionParser, OptionGroup


class EpilogParser(OptionParser):
    def format_epilog(self, formatter):
        return self.epilog


def delete_parser():
    """Return the command-line parser for the delete command."""
    usage = "usage: %prog [tx_options] delete OPTION [OPTIONS]"
    description = (
        "This command deletes translations for a "
        "resource in the remote server."
    )
    epilog = (
        "\nExamples:\n"
        "To delete a translation:\n"
        "$ tx delete -r project.resource -l <lang_code>\n\n"
        "To delete a resource:\n  $ tx delete -r project.resource\n"
    )
    parser = EpilogParser(usage=usage, description=description, epilog=epilog)
    parser.add_option(
        "-r", "--resource", action="store", dest="resources", default=None,
        help="Specify the resource you want to delete (defaults to all)"
    )
    parser.add_option(
        "-l", "--language", action="store", dest="languages",
        default=None, help="Specify the translation you want to delete"
    )
    parser.add_option(
        "--skip", action="store_true", dest="skip_errors", default=False,
        help="Don't stop on errors."
    )
    parser.add_option(
        "-f", "--force", action="store_true", dest="force_delete",
        default=False, help="Delete an entity forcefully."
    )
    return parser


def help_parser():
    """Return the command-line parser for the help command."""
    usage = "usage: %prog help command"
    description = "Lists all available commands in the transifex command "\
        "client. If a command is specified, the help page of the specific "\
        "command is displayed instead."

    parser = OptionParser(usage=usage, description=description)
    return parser


def init_parser():
    """Return the command-line parser for the init command."""
    usage = "usage: %prog [tx_options] init <path>"
    description = "This command initializes a new project for use with "\
        "Transifex. It is recommended to execute this command in the "\
        "top level directory of your project so that you can include "\
        "all files under it in transifex. If no path is provided, the "\
        "current working dir will be used."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("--host", action="store", dest="host", default=None,
                      help="Specify a default Transifex host.")
    parser.add_option("--user", action="store", dest="user", default=None,
                      help="Specify username for Transifex server.")
    parser.add_option("--pass", action="store", dest="password", default=None,
                      help="Specify password for Transifex server.")
    parser.add_option(
        "--force-save",
        action="store_true",
        dest="save",
        default=False,
        help="Override .transifexrc file with the given credentials."
    )

    parser.add_option("--token", action="store", dest="token", default=None,
                      help="Specify an api token.\nYou can get one from"
                      " user's settings")
    return parser


def pull_parser():
    """Return the command-line parser for the pull command."""
    usage = "usage: %prog [tx_options] pull [options]"
    description = "This command pulls all outstanding changes from the remote "\
        "Transifex server to the local repository. By default, only the "\
        "files that are watched by Transifex will be updated but if you "\
        "want to fetch the translations for new languages as well, use the "\
        "-a|--all option. (Note: new translations are saved in the .tx folder "\
        "and require the user to manually rename them and add then in "\
        "Transifex using the set_translation command)."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-l", "--language", action="store", dest="languages",
                      default=[], help="Specify which translations "
                      "you want to pull (defaults to all)")
    parser.add_option("-r", "--resource", action="store", dest="resources",
                      default=[], help="Specify the resource for which you "
                      "want to pull the translations (defaults to all)")
    parser.add_option("-a", "--all", action="store_true", dest="fetchall",
                      default=False, help="Fetch all translation files from "
                      "server (even new ones)")
    parser.add_option("-s", "--source", action="store_true",
                      dest="fetchsource", default=False,
                      help="Force the fetching of the source file (default: "
                      "False)")
    parser.add_option("-f", "--force", action="store_true", dest="force",
                      default=False, help="Force download of translations "
                      "files.")
    parser.add_option("--skip", action="store_true", dest="skip_errors",
                      default=False, help="Don't stop on errors. Useful when "
                      "pushing many files concurrently.")
    parser.add_option("--disable-overwrite", action="store_false",
                      dest="overwrite", default=True,
                      help="By default transifex will fetch new translations "
                      "files and replace existing ones. Use this flag if you "
                      "want to disable this feature")
    parser.add_option("--minimum-perc", action="store", type="int",
                      dest="minimum_perc", default=0,
                      help="Specify the minimum acceptable percentage of "
                      "a translation in order to download it.")
    parser.add_option("--pseudo", action="store_true", dest="pseudo",
                      default=False, help="Apply this option to download "
                      "a pseudo file.")
    parser.add_option(
        "--mode", action="store", dest="mode", help=(
            "Specify the mode of the translation file to pull (e.g. "
            "'reviewed'). See http://bit.ly/pullmode for available values."
        )
    )
    parser.add_option("-x", "--xliff", action="store_true", dest="xliff",
                      default=False, help="Apply this option to download "
                      "file as xliff.")
    return parser


def push_parser():
    """Return the command-line parser for the push command."""
    usage = "usage: %prog [tx_options] push [options]"
    description = "This command pushes all local files that have been added to "\
        "Transifex to the remote server. All new translations are merged "\
        "with existing ones and if a language doesn't exists then it gets "\
        "created. If you want to push the source file as well (either "\
        "because this is your first time running the client or because "\
        "you just have updated with new entries), use the -f|--force option. "\
        "By default, this command will push all files which are watched by "\
        "Transifex but you can filter this per resource or/and language. "
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-l", "--language", action="store", dest="languages",
                      default=None, help="Specify which translations you "
                      "want to push (defaults to all)")
    parser.add_option("-r", "--resource", action="store", dest="resources",
                      default=None, help="Specify the resource for which you "
                      "want to push the translations (defaults to all)")
    parser.add_option("-f", "--force", action="store_true",
                      dest="force_creation", default=False,
                      help="Push source files without checking modification "
                      "times.")
    parser.add_option("--skip", action="store_true", dest="skip_errors",
                      default=False, help="Don't stop on errors. "
                      "Useful when pushing many files concurrently.")
    parser.add_option("-s", "--source", action="store_true",
                      dest="push_source", default=False,
                      help="Push the source file to the server.")

    parser.add_option("-t", "--translations", action="store_true",
                      dest="push_translations", default=False,
                      help="Push the translation files to the server")
    parser.add_option("--no-interactive", action="store_true",
                      dest="no_interactive", default=False,
                      help="Don't require user input when forcing a push.")
    parser.add_option("-x", "--xliff", action="store_true", dest="xliff",
                      default=False, help="Apply this option to upload "
                      "file as xliff.")
    return parser


def set_parser():
    """Return the command-line parser for the set command."""
    usage = "usage: %prog [tx_options] set [options] [args]"
    description = "This command can be used to create a mapping between files "\
        "and projects either using local files or using files from a remote "\
        "Transifex server."
    epilog = "\nExamples:\n"\
        "To set the source file:\n  $ tx set -r project.resource --source -l en <file>\n\n"\
        "To set a single translation file:\n  $ tx set -r project.resource -l de <file>\n\n"\
        "To automatically detect and assign the source files and translations:\n"\
        " $ tx set --auto-local -r project.resource 'expr' --source-lang en\n\n"\
        "To set a specific file as a source and auto detect translations:\n"\
        " $ tx set --auto-local -r project.resource 'expr' --source-lang en "\
        "--source-file <file>\n\n"\
        "To set a remote resource/project:\n"\
        "  $ tx set --auto-remote <transifex-url>\n"
    parser = EpilogParser(usage=usage, description=description, epilog=epilog)
    parser.add_option("--auto-local", action="store_true",
                      dest="local", default=False,
                      help="Used when auto configuring local project.")
    parser.add_option("--auto-remote", action="store_true",
                      dest="remote", default=False,
                      help="Used when adding remote files from Transifex "
                      "server.")
    parser.add_option("-r", "--resource", action="store", dest="resource",
                      default=None,
                      help="Specify the slug of the resource that you're "
                      "setting up (This must be in the following format: "
                      "`project_slug.resource_slug`).")
    parser.add_option(
        "--source", action="store_true", dest="is_source", default=False,
        help=(
            "Specify that the given file is a source file "
            "[doesn't work with the --auto-* commands]."
        )
    )
    parser.add_option("-l", "--language", action="store", dest="language",
                      default=None,
                      help="Specify which translations you want to pull "
                      "[doesn't work with the --auto-* commands].")
    parser.add_option("-t", "--type", action="store", dest="i18n_type",
                      help=("Specify the i18n type of the resource(s). "
                            "This is only needed, if the resource(s) does not "
                            "exist yet in Transifex. For a list of "
                            "available i18n types, see "
                            "http://docs.transifex.com/formats/"
                            ))
    parser.add_option("--minimum-perc", action="store", dest="minimum_perc",
                      help=("Specify the minimum acceptable percentage "
                            "of a translation in order to download it."
                            ))
    parser.add_option(
        "--mode", action="store", dest="mode", help=(
            "Specify the mode of the translation file to pull (e.g. "
            "'reviewed'). See http://bit.ly/pullmode for the "
            "available values."
        )
    )
    group = OptionGroup(parser, "Extended options", "These options can only "
                                "be used with the --auto-local command.")
    group.add_option("-s", "--source-language", action="store",
                     dest="source_language", default=None,
                     help="Specify the source language of a resource "
                     "[requires --auto-local].")
    group.add_option("-f", "--source-file", action="store", dest="source_file",
                     default=None, help="Specify the source file of a "
                     "resource [requires --auto-local].")
    group.add_option("--execute", action="store_true", dest="execute",
                     default=False, help="Execute commands "
                     "[requires --auto-local].")
    parser.add_option_group(group)
    return parser


def status_parser():
    """Return the command-line parser for the status command."""
    usage = "usage: %prog [tx_options] status [options]"
    description = "Prints the status of the current project by reading the "\
                  "data in the configuration file."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-r", "--resource", action="store", dest="resources",
                      default=[], help="Specify resources")
    return parser


def parse_csv_option(option):
    """Return a list out of the comma-separated option or an empty list."""
    if option:
        return option.split(',')
    else:
        return []
