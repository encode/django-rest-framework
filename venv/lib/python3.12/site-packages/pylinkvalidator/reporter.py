"""
Contains the reporting functions
"""
from __future__ import unicode_literals, absolute_import, print_function

import codecs
import re
import smtplib
import sys

from email.mime.text import MIMEText

from pylinkvalidator.compat import StringIO
from pylinkvalidator.models import (
    REPORT_TYPE_ERRORS, REPORT_TYPE_ALL, FORMAT_PLAIN)


PLAIN_TEXT = "text/plain"
HTML = "text/html"

WHITESPACES = re.compile(r"\s+")


EMAIL_HEADER = "from: {0}\r\nsubject: {1}\r\nto: {2}\r\nmime-version: 1.0\r\n"\
               "content-type: {3}\r\n\r\n{4}"


def close_quietly(a_file):
    """Closes a file and does not report an error."""
    try:
        if a_file:
            a_file.close()
    except Exception:
        pass


def report(site, config, total_time, logger=None):
    """Prints reports to console, file, and email."""
    output_files = []
    output_file = None
    email_file = None

    if config.options.output:
        output_file = codecs.open(config.options.output, "w", "utf-8")
        output_files.append(output_file)

    if config.options.smtp:
        email_file = StringIO()
        output_files.append(email_file)

    if config.options.console or not output_files:
        output_files.append(sys.stdout)

    try:
        if config.options.format == FORMAT_PLAIN:
            _write_plain_text_report(site, config, output_files, total_time)
    except Exception:
        if logger:
            logger.exception("An exception occurred while writing the report")

    if output_file:
        close_quietly(output_file)

    if email_file:
        send_email(email_file, site, config)


def _write_plain_text_report(site, config, output_files, total_time):
    start_urls = ",".join((start_url_split.geturl() for start_url_split in
                           site.start_url_splits))

    total_urls = len(site.pages)
    total_errors = len(site.error_pages)

    if not site.is_ok:
        global_status = "ERROR"
        error_summary = "with {0} error(s) ".format(total_errors)
    else:
        global_status = "SUCCESS"
        error_summary = ""

    oprint("{0} Crawled {1} urls {2}in {3:.2f} seconds".format(
        global_status, total_urls, error_summary, total_time),
        files=output_files)

    pages = {}

    if config.options.report_type == REPORT_TYPE_ERRORS:
        pages = site.error_pages
    elif config.options.report_type == REPORT_TYPE_ALL:
        pages = site.pages

    if pages:
        oprint("\n  Start URL(s): {0}".format(start_urls), files=output_files)

        for page in pages.values():
            oprint("\n  {0}: {1}".format(
                page.get_status_message(), page.url_split.geturl()),
                files=output_files)
            for source in page.sources:
                oprint("    from {0}".format(
                    source.origin.geturl()), files=output_files)
                if config.options.show_source:
                    oprint("      {0}".format(
                        truncate(source.origin_str)), files=output_files)


def oprint(message, files):
    """Prints to a sequence of files."""
    for file in files:
        print(message, file=file)


def truncate(value, size=72):
    """Truncates a string if its length is higher than size."""
    value = value.replace("\n", " ").replace("\r", "").replace("\t", " ")
    value = value.strip()
    value = WHITESPACES.sub(" ", value)

    if len(value) > size:
        value = "{0}...".format(value[:size-3])

    return value


def send_email(email_file, site, config):
    options = config.options
    if options.subject:
        subject = options.subject
    else:
        if site.is_ok:
            subject = "SUCCESS - {0}".format(site.start_url_splits[0].geturl())
        else:
            subject = "ERROR - {0}".format(site.start_url_splits[0].geturl())

    if options.from_address:
        from_address = options.from_address
    else:
        from_address = "pylinkvalidator@localhost"

    if not options.address:
        print("Email address must be specified when using smtp.")
        sys.exit(1)

    addresses = options.address.split(",")

    msg = MIMEText(email_file.getvalue(), 'plain', "UTF-8")

    msg['From'] = from_address
    msg['To'] = ", ".join(addresses)
    msg['Subject'] = subject

    smtpserver = smtplib.SMTP(options.smtp, options.port)

    if options.tls:
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo

    if options.smtp_username and options.smtp_password:
        smtpserver.login(options.smtp_username, options.smtp_password)

    smtpserver.sendmail(from_address, addresses, msg.as_string())

    smtpserver.quit()
