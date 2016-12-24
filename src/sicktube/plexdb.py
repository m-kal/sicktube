from pprint import pprint
import os
import platform
import sqlite3
import uuid
import json

class PlexDB:

    PLEX_DB_FILENAME = 'com.plexapp.plugins.library.db'
    PLEX_DB_PLAYLIST_TYPE_ID = 15
    PLEX_DB_ADMIN_USER_ID = 1

    db_dir = None
    db_conn = None

    def __init__(self, dir=None):
        self.db_dir = dir
        self.db_conn = None

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @staticmethod
    def get_plex_db_path(dir=None):
        if dir is not None:
            fullpath = os.path.join(dir, PlexDB.PLEX_DB_FILENAME)
            if os.path.exists(fullpath):
                print fullpath
                return fullpath

        if platform.system() == 'Windows':
            pprint(platform.system())
            for k,v in os.environ.items():
                print k
                print v
                print ""

    @staticmethod
    def plex_order_to_idx(order):
        return (order/1000)-1

    @staticmethod
    def idx_to_plex_order(idx):
        return (idx + 1) * 1000

    def get_db_full_path(self):
        return os.path.join(self.db_dir, PlexDB.PLEX_DB_FILENAME)

    def connect(self):
        if self.db_conn:
            return True

        try:
            self.db_conn = sqlite3.connect(self.get_db_full_path())
            self.db_conn.row_factory = PlexDB.dict_factory
            #self.db_conn.row_factory = sqlite3.Row
            return True
        except Exception as ex:
            print(ex)
            return False

    def disconnect(self):
        if self.db_conn:
            self.db_conn.close()


    def get_playlist_by_id(self, id):
        cur = self.db_conn.cursor()
        cur.execute(
            'SELECT mi.* '
            'FROM metadata_items AS mi '
            'WHERE mi.metadata_type = ? '
            'AND mi.id = ?',
            (self.PLEX_DB_PLAYLIST_TYPE_ID, id,))

        return cur.fetchone()

    def get_playlists(self, load_items=True):
        playlists = []
        if not self.connect():
            return playlists

        cur_playlists = self.db_conn.cursor()
        cur_playlists.execute(
            'SELECT * '
            'FROM metadata_items '
            'WHERE metadata_type=?',
            (15,))

        for playlist in cur_playlists.fetchall():
            playlist['_items'] = []
            cur_playlist = self.db_conn.cursor()
            cur_playlist.execute(
                'SELECT mdi.*, pqg.`order`, COALESCE (mdi.duration, mi.duration) as duration '
                'FROM play_queue_generators AS pqg '
                'JOIN metadata_items AS mdi ON (mdi.id == pqg.metadata_item_id) '
                'JOIN media_items AS mi ON (mi.metadata_item_id == mdi.id) '
                'WHERE pqg.playlist_id = ?',
                (playlist['id'],))

            if load_items:
                rounded_duration = 0
                real_duration = 0
                for metadata_item in cur_playlist.fetchall():
                    rounded = int(metadata_item['duration']/1000)
                    absolute = int(metadata_item['duration'])
                    rounded_duration += rounded
                    real_duration += absolute

                    playlist['_items'].append(metadata_item)

            playlists.append(playlist)

        return playlists

    def playlist_exists(self, title):
        for plist in self.get_playlists(False):
            if title == plist['title']:
                return True
        return False

    @staticmethod
    def sql_create_playlist_metadata_item(section_id, title, guid=None, extra_data=None, title_sort=None, absolute_index=10):
        if guid is None:
            guid = 'com.plexapp.agents.sicktube://' + str(uuid.uuid1())

        if extra_data is None:
            extra_data = 'pv%3AdurationInSeconds=1&pv%3AsectionIDs=%d'.format(section_id)

        if title_sort is None:
            title_sort = title
        #library_section_id,
        sql = "INSERT INTO metadata_items (added_at, created_at, updated_at, metadata_type, guid, media_item_count, title, title_sort, duration, extra_data, absolute_index) VALUES((DATETIME('now')), (DATETIME('now')), (DATETIME('now')), ?, ?, ?, ?, ?, ?, ?, ?)"
        params = (PlexDB.PLEX_DB_PLAYLIST_TYPE_ID, guid, 0, title, title_sort, 0, extra_data, absolute_index)

        return (sql, params)

    def update_playlist_entries(self, playlist_id, plex_media_entries=[]):
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist is None:
            print("Playlist not found")

        # Assign playlist items to the playlist
        # TODO: decide if we should override or validate ordering here
        cur = self.db_conn.cursor()
        duration_ms = 0
        media_entry_count = len(plex_media_entries)
        idx = 0
        for media_entry in plex_media_entries:
            duration_ms += media_entry['duration']
            #order = PlexDB.idx_to_plex_order(media_entry['index'])
            order = PlexDB.idx_to_plex_order(idx)
            # Check if this media item already exists or not in play_queue_generators
            cur.execute('SELECT id FROM play_queue_generators WHERE playlist_id=? AND metadata_item_id=?', (playlist_id, media_entry['id']))
            pqg_id = cur.fetchone()
            if pqg_id is not None:
                # print("pqg_id: %d" % pqg_id)
                cur.execute('UPDATE play_queue_generators SET order=? WHERE id=?', (order, pqg_id))
            else:
                # print("pqg_id not found: %d and %d" % (playlist_id, media_entry['id']))
                cur.execute("INSERT INTO play_queue_generators (created_at, updated_at, playlist_id, metadata_item_id, `order`) VALUES ((DATETIME('now')), (DATETIME('now')), ?, ?, ?)" , (playlist_id, media_entry['id'], order))

            idx += 1

        cur.execute(
            'UPDATE metadata_items '
            'SET duration=?, media_item_count=? '
            'WHERE id=?',
            (duration_ms/1000, media_entry_count, playlist['id']))

        self.db_conn.commit()

    def create_playlist(self, title=None, id=None, plex_media_entries=[]):
        if len(plex_media_entries) is 0:
            return None

        playlist = None
        playlist_id = None
        if id is not None:
            playlist = self.get_playlist_by_id(id)
        elif title is not None:
            playlist_id = self.get_playlist_id_by_title(title)
            if playlist_id is not None:
                playlist = self.get_playlist_by_id(playlist_id)
        else:
            return None

        if playlist is None:
            cur = self.db_conn.cursor()
            library_section_id = plex_media_entries[0]['library_section_id']
            print("Creating playlist: %s | %s" % (title,id))
            # TODO: Do validation checks

            # Create the playlist metadata_item
            (sql, params) = PlexDB.sql_create_playlist_metadata_item(library_section_id, title)
            cur.execute(sql, params)
            playlist_id = cur.lastrowid

            # Give user's account access to the metadata_item
            self.give_playlist_access(playlist_id, cur=cur)
            self.db_conn.commit()

            return playlist_id

    def get_playlist_id_by_title(self, title):
        cur = self.db_conn.cursor()
        cur.execute(
            'SELECT mi.id, mi.title '
            'FROM metadata_items AS mi '
            'WHERE mi.metadata_type = ? '
            'AND mi.title = ?',
            (self.PLEX_DB_PLAYLIST_TYPE_ID, title,))

        res = cur.fetchone()
        if res is not None:
            return res['id']

        return None

    def get_playlist_order(self, metadata_item_id):
        cur = self.db_conn.cursor()
        cur.execute(
            'SELECT pqg.`order` '
            'FROM play_queue_generators AS pqg '
            'WHERE pqg.metadata_item_id = ? ',
            (metadata_item_id,))

        order = None
        for res in cur.fetchall():
            order = int(res['order'])

        return order

    def give_playlist_access(self, playlist_id, account_id=PLEX_DB_ADMIN_USER_ID, cur=None):
        if cur is None:
            cur = self.db_conn.cursor()

        cur.execute(
            'SELECT mia.* '
            'FROM metadata_item_accounts AS mia '
            'WHERE mia.account_id=? '
            'AND metadata_item_id=?',
            (int(account_id), int(playlist_id)))

        if cur.fetchone() is None:
            cur.execute('INSERT INTO metadata_item_accounts (account_id, metadata_item_id) VALUES (?, ?)',
                        (int(account_id), int(playlist_id)))
            id = cur.lastrowid
            if id is None:
                print("failed to insert...")

    def find_media_entry_from_id(self, id):
        cur = self.db_conn.cursor()
        cur.execute(
            'SELECT mdi.*, mi.duration '
            'FROM metadata_items AS mdi '
            'JOIN media_items AS mi ON (mi.metadata_item_id == mdi.id) '
            'WHERE mdi.id = ? ',
            (id,))

        res = cur.fetchone()

        return res

    def find_media_entry_from_info_json(self, info_json):
        '''Note: This uses title so it needs to be updated to avoid incorrect matching / needs more constraints.'''
        cur = self.db_conn.cursor()
        cur.execute(
            'SELECT mdi.*, mi.duration '
            'FROM metadata_items AS mdi '
            'JOIN media_items AS mi ON (mi.metadata_item_id == mdi.id) '
            'WHERE mdi.title = ? ',
            (info_json['title'],))

        best_diff = None
        best_res = None
        for res in cur.fetchall():
            dur = int(res['duration'])/1000
            diff = abs(info_json['duration'] - dur)
            if (best_diff is None) or (diff < best_diff):
                best_diff = diff
                best_res = res

        return best_res