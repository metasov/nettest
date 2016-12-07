import sys
import logging
import csv
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from datetime import date, timedelta

import emails

from nettest.config import NettestConfig
from nettest.storage import NettestStorage


def html_report_generator(keys, data):
    all_tests = len(data)
    failed_dns_tests = len(filter(lambda t: t['dns'] is None, data))
    if all_tests:
        percent_of_success = 100.0 * (all_tests - failed_dns_tests) / all_tests
    else:
        percent_of_success = 0.0

    yield "<html><head><title></title></head><body>"
    yield "Percent of success: %.2f <br/>" % percent_of_success
    yield "<table><tr>"
    for key in keys:
        if key in ('rowid',):
            continue
        title = key.replace("_", " ").capitalize()
        yield "<th>" + title + "</th>"
    yield "</tr>"

    for row in data:
        yield"<tr>"
        for key in keys:
            if key in ('rowid',):
                continue
            
            yield"<td>"
            
            if key in ('datetime',):
                yield str(row[key])
            elif row[key] is None:
                yield '<span style="color: red">FAILED</span>'
            else:
                yield '%.3f' % row[key]

            yield "</td>"
        yield "</tr>"
    yield "</body></html>"

def make_html_report(keys, data):
    return "".join(html_report_generator(keys, data))

def make_csv_report(keys, data):
    result = StringIO.StringIO()
    filtered_keys = [k for k in keys if k != 'rowid']
    writer = csv.DictWriter(result, filtered_keys)
    writer.writeheader()
    for row in data:
        new_row = {}
        for key in filtered_keys:
            if key in ('rowid',):
                continue
            elif key in ('datetime',): 
                new_row[key] = row[key]
            elif row[key] is None:
                new_row[key] = 'FAILED'
            else:
                new_row[key] = '%.3f' % row[key]
        writer.writerow(new_row)
    result.seek(0)
    return result

def send_report(config):
    log = logging.getLogger(__name__)
    email_to = map(str.strip, config.get('email.to').split(','))
    email_from_email = config.get('email.from_email')
    email_from_name = config.get('email.from_name')
    host = config.get('smtp.host')
    port = config.get('smtp.port')
    ssl = bool(config.getint('smtp.use_ssl'))
    tls = bool(config.getint('smtp.use_tls'))
    user = config.get('smtp.user')
    password = config.get('smtp.password')

    day = date.today()
    if config.get('email.day') == 'yesterday':
        day -= timedelta(days=1)
    elif config.get('email.day') != 'today':
        raise ConfigReadError(
            'email.day should be only "today" or "yesterday" ')
    storage = NettestStorage(config, read_only=True)
    data = storage.get_entries_for_date(day)
    keys = storage.keys()
    
    message = emails.html(
        html = make_html_report(keys, data),
        mail_from=(email_from_name, email_from_email),
        subject="Nettest report for %s" % day)

    message.attach(
        data=make_csv_report(keys, data),
        filename='nettest_report-%s.csv' % day.strftime('%Y-%m-%d'))
    
    for address in email_to:
        response = message.send(
            to=(address, address),
            smtp={
                'host': host,
                'port': port,
                'ssl': ssl,
                'tls': tls,
                'user': user,
                'password': password})

        if response.status_code != 250:
            log.error(
                'Cannot send email to %s. Response: %s',
                address, response)


if __name__ == '__main__':
    try:
        config_name = sys.argv[1]
    except IndexError:
        sys.stderr.write('Please specify config file name\n')
        exit(998)

    config = NettestConfig()
    config.read(config_name)

    logging.config.fileConfig(
        config_name,
        disable_existing_loggers=False)
    
    send_report(config)
