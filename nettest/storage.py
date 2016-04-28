import sqlite3

class NettestStorage(object):
    def __init__(self, config, read_only=False):
        self.config = config
        filename = config.get('storage.filename')
        self.db = sqlite3.connect(filename)
        self.http_keys = tuple(
            k.strip() for k in config.get('http.keys').split(','))
        self.ftp_keys = tuple(
            k.strip() for k in config.get('ftp.keys').split(','))
        self.cursor = self.db.cursor()
        self._create_tables()
        self._read_only = read_only
        if not read_only:
           self._rowid = self._new_entry()

    @property
    def rowid(self):
        return self._rowid

    @property
    def datetime(self):
        if self._read_only:
            return None
        self.cursor.execute("""
            SELECT datetime FROM tests
            WHERE rowid = %s
        """, self._rowid)
        datetime = self.cursor.fetchone()[0]
        self.db.rollback()
        return datetime

    @staticmethod
    def _escape(name):
        result = name.encode("utf-8", "ignore")
        result = result.decode("utf-8")
        result = result.replace("\"", "\"\"")
        return result

    def _create_tables(self):
        http_keys = [self._escape(key) for key in self.http_keys]
        ftp_keys = [self._escape(key) for key in self.ftp_keys]
        
        substitutes = {
            "http": ",".join("http_%s" % k for k in http_keys),
            "ftp_up": ",".join("ftp_down_%s" % k for k in ftp_keys),
            "ftp_down": ",".join("ftp_up_%s" % k for k in ftp_keys)
        }
        sql = """
            CREATE TABLE IF NOT EXISTS tests (
                rowid INTEGER PRIMARY KEY,
                datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interface REAL DEFAULT NULL,
                dns REAL DEFAULT NULL,
                %(http)s,
                %(ftp_down)s,
                %(ftp_up)s
            );
        """ % substitutes
        
        self.cursor.execute(sql)
        self.db.commit()

    def _new_entry(self):
        self.cursor.execute("""
            INSERT INTO tests (interface) VALUES (NULL);
        """)
        rowid = self.cursor.lastrowid
        self.db.commit()
        return rowid

    def update(self, interface, dns, http, ftp_down, ftp_up):
        if self._read_only:
            return
        
        values =  [interface, dns]
       
        http = http or [None,] * len(self.http_keys)
        ftp_down = ftp_down or [None,] * len(self.ftp_keys)
        ftp_up = ftp_up or [None,] * len(self.ftp_keys)

        values.extend(http)
        values.extend(ftp_down)
        values.extend(ftp_up)

        values.append(self._rowid)
        
        http_keys = [self._escape(key) for key in self.http_keys]
        ftp_keys = [self._escape(key) for key in self.ftp_keys]

        substitutes = {
            "http": ",".join("http_%s = ?" % k for k in http_keys),
            "ftp_down": ",".join("ftp_down_%s = ?" % k for k in ftp_keys),
            "ftp_up": ",".join("ftp_up_%s = ?" % k for k in ftp_keys)
        }
        sql = """
            UPDATE tests SET
                interface = ?,
                dns = ?,
                %(http)s,
                %(ftp_down)s,
                %(ftp_up)s
            WHERE
                rowid = ?;
        """ % substitutes

        self.cursor.execute(sql, values)
        self.db.commit()

    def keys(self):
        result = ['rowid', 'datetime', 'interface', 'dns']
        for key in self.http_keys:
            result.append('http_'+key)
        for key in self.ftp_keys:
            result.append('ftp_down_'+key)
            result.append('ftp_up_'+key)
        return result

        
    def get_entries_for_date(self, date):
        keys = self.keys()
        sql_keys = ",".join(self._escape(k) for k in self.keys())
        
        sql = """
            SELECT %s
            FROM tests
            WHERE date(datetime) = ?
        """ % sql_keys
        self.cursor.execute(sql, (date,))
        
        data = []
        for row in self.cursor.fetchall():
            result = {}
            for index, key in enumerate(keys):
                result[key] = row[index]
            data.append(result)
        return data

