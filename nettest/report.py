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

def make_html_report(data):
    chunks = [
        "<html><head><title></title></head>"
        "<body><table><tr>"
        " <th>Timestamp</th><th>Interface+DHCP up (sec)</th>"
        " <th>Http download (bits/s)</th><th>FTP download (bits/s)</th>"
        " <th>FTP upload (bits/s)</th>"
        "</tr>"]
    for row in data:
        new_row = {'datetime': row['datetime']}
        for key in ['interface', 'http', 'ftp_down', 'ftp_up']:
            if row[key] is None:
                new_row[key] = 'FAILED'
            else:
                new_row[key] = '%.3f' % row[key]
        chunks.append(
            "<tr>"
            "<td>%(datetime)s</td>"
            "<td>%(interface)s</td>"
            "<td>%(http)s</td>"
            "<td>%(ftp_down)s</td>"
            "<td>%(ftp_up)s</td>"
            "</tr>" % new_row)
    chunks.append("</body></html>")

    return "\n".join(chunks)

def make_csv_report(data):
    result = StringIO.StringIO()
    writer = csv.DictWriter(
        result,
        ['datetime', 'interface', 'http', 'ftp_down', 'ftp_up'])
    writer.writeheader()
    for row in data:
        new_row = {'datetime': row['datetime']}
        for key in ['interface', 'http', 'ftp_down', 'ftp_up']:
            if row[key] is None:
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
    
    message = emails.html(
        html = make_html_report(data),
        mail_from=(email_from_name, email_from_email),
        subject="Nettest report for %s" % day)

    message.attach(
        data=make_csv_report(data),
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
