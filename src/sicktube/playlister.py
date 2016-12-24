from plexdb import PlexDB
import json
import os
import sicktube

class Playlister:
    def __init__(self, db_dir):
        self.db_dir = db_dir

    @staticmethod
    def keys_in_dict(dict, keys):
        for k in keys:
            if k not in dict:
                return False
        return True

    @staticmethod
    def fill_playlist_gaps(pdb, media_entries, playlist_metadatas):
        """Fills in missing media_entries using entries through reverse-lookup.

        Uses a valid entry in media_entries to extract the playlist_id which is passed to Sicktube's static MetadataFromUrl.
        The returned metadata_dict will return a sorted list of playlist entries which can be used to attempt a lookup
        of the playlist entry in the plexdb.
        Note: this requires that the playlist gaps match perfectly with the returned live results
        Note: Will need to switch off idx lookups and pass in some constraints
        TODO: All title-based mapping needs to be more constrained"""
        idx = 0
        lookup_idx = None
        for pl_me in playlist_metadatas:
            if pl_me is not None:
                lookup_idx = idx
                break
            idx += 1

        if lookup_idx is None:
            #print("lookup_idx is None")
            return None

        me = media_entries[lookup_idx]
        md = playlist_metadatas[lookup_idx]
        #print("Filling gaps with %d" % me['id'])
        (metadata_dict, ytdl) = sicktube.Sicktube.MetadataFromUrl(md['playlist_id'])

        idx = -1
        for pl_me in playlist_metadatas:
            idx += 1
            if pl_me is not None:
                continue

            metadata = metadata_dict['entries'][idx]
            if metadata is None:
                #print("metadata is none, not sure what to do...")
                return None

            media_entry = pdb.find_media_entry_from_info_json(metadata)
            if media_entry is None:
                #print("media_entry is none, not sure what to do...")
                return None

            media_entries[idx] = media_entry

    def file_path_to_metadata(self, file_path):
        if os.path.exists(file_path):
            return json.load(open(file_path))
        return None
    # def update_playlist_position(plexdb_metadata_item):

    def insert_playlist_entry(plexdb_metadata_item, idx):
        order = PlexDB.idx_to_plex_order(idx)

    def file_paths_to_metadata(self, file_paths=[]):
        metadatas = []
        for file_path in file_paths:
            metadata = self.file_path_to_metadata(file_path)
            if metadata is not None:
                metadata['_file_path'] = file_path
                metadatas.append(metadata)
        return metadatas

    def create_plexdb_playlist(self, title, file_paths=[]):
        # Connect to the database
        pdb = PlexDB(self.db_dir)
        if not pdb.connect():
            print("Unable to connect to database")
            return None

        # Load .info.json files from file paths and do basic validation
        metadata = []
        playlist_reported_entry_counts = {}
        raw_metadata = self.file_paths_to_metadata(file_paths)
        for rmd in raw_metadata:
            if Playlister.keys_in_dict(rmd, ['n_entries', 'playlist_index']):
                metadata.append(rmd)
                playlist_reported_entry_counts[rmd['n_entries']] = True
        # Ensure all metadata agrees with the playlist count
        # Note: this is needed to contextualize updated playlists in the future
        all_counts_equal = (len(playlist_reported_entry_counts.keys()) == 1)
        n_entries = playlist_reported_entry_counts.keys()[0]

        # Look up the playlist by the title
        # TODO: add in section for library_Section lookup
        playlist_id = pdb.get_playlist_id_by_title(title)
        playlist_found = (playlist_id is not None)

        # Validation flags
        all_orders_matched = True

        playlist_media_entries = [None] * n_entries
        playlist_metadatas = [None] * n_entries
        for item in metadata:
            item_playlist_idx = item['playlist_index'] - 1
            expected_order = PlexDB.idx_to_plex_order(item_playlist_idx)
            media_entry = pdb.find_media_entry_from_info_json(item)

            if media_entry is not None:
                playlist_media_entries[item_playlist_idx] = media_entry
                playlist_metadatas[item_playlist_idx] = item
                playlist_order = pdb.get_playlist_order(media_entry['id'])
                all_orders_matched &= (expected_order == playlist_order)

        all_orders_matched &= all_counts_equal
        all_existing_db_entries = (None not in playlist_media_entries)

        if not all_existing_db_entries:
            # Try to fill any gaps my using Sicktube's static MetadataFromUrl method
            Playlister.fill_playlist_gaps(pdb, playlist_media_entries, playlist_metadatas)
            # Update the all-found var as playlist_media_entries may be modified
            all_existing_db_entries = (None not in playlist_media_entries)

        if not playlist_found and all_existing_db_entries:
            # Give PlexDB the media_entries to construct a playlist from
            playlist_id = pdb.create_playlist(title, None, playlist_media_entries)
            if playlist_id is None:
                print("Failed to create playlist")
                return
            pdb.update_playlist_entries(playlist_id, playlist_media_entries)

        elif playlist_found and all_orders_matched:
            print("Playlist: %s is 100%% in-tact" % title)

        elif playlist_found and all_existing_db_entries:
            print("Playlist found but something else")
            pdb.update_playlist_entries(playlist_id, playlist_media_entries)