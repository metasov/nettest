import sqlite3

class NettestStorage(object):
    def __init__(self, config, read_only=False):
        self.config = config
        filename = config.get('storage.filename')
        self.db = sqlite3.connect(filename)
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
            WHERE id = %s
        """, self._rowid)
        datetime = self.cursor.fetchone()[0]
        self.db.rollback()
        return datetime

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY,
                datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interface REAL DEFAULT NULL,
                http REAL DEFAULT NULL,
                ftp_down REAL DEFAULT NULL,
                ftp_up REAL DEFAULT NULL
            );
        """)
        self.db.commit()

    def _new_entry(self):
        self.cursor.execute("""
            INSERT INTO tests (interface) VALUES (NULL);
        """)
        rowid = self.cursor.lastrowid
        self.db.commit()
        return rowid

    def update(self, interface, http, ftp_down, ftp_up):
        if self._read_only:
            return
        self.cursor.execute("""
            UPDATE tests SET
                interface = ?,
                http = ?,
                ftp_down = ?,
                ftp_up = ?
            WHERE
                id = ?;
        """,
        [interface, http, ftp_down, ftp_up, self._rowid])
        self.db.commit()

    def get_entries_for_date(self, date):
        data = []
        self.cursor.execute("""
            SELECT id, datetime, interface, http, ftp_down, ftp_up
            FROM tests
            WHERE date(datetime) = ?
        """, (date,))
        for row in self.cursor.fetchall():
            rowid, datetime, interface, http, ftp_down, ftp_up = row
            data.append({
                'id': rowid,
                'datetime': datetime,
                'interface': interface,
                'http': http,
                'ftp_down': ftp_down,
                'ftp_up': ftp_up})
        return data

