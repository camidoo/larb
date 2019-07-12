# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# sheets.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import logging
import re as rep

# -----------------------------------------------------------------------------
# class SheetsCache
# -----------------------------------------------------------------------------

class SheetsCache:

    # -------------------------------------------------------------------------
    # ctor

    def __init__(self, cache_store_dir, credentials_path, token_path, sheet_id):
        self.cache_store_path_en = cache_store_dir + "/resource_cache_en.dat"
        self.cache_store_path_de = cache_store_dir + "/resource_cache_de.dat"
        self.cache_store_path_islands = cache_store_dir + "/islands_cache.dat"
        self.cache_store_path_grids = cache_store_dir + "/grids_cache.dat"
        self.log = logging.getLogger(__name__)

        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.token_path = token_path

        self.credentials = None
        self.service = None

        self.scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

        self.resource_map_en = {}
        self.resource_map_de = {}
        self.all_islands = list()
        self.all_grids = list()

        if (os.path.exists(self.cache_store_path_en) 
            and os.path.exists(self.cache_store_path_de) 
            and os.path.exists(self.cache_store_path_islands) 
            and os.path.exists(self.cache_store_path_grids)):

            self.log.info("Loading resource cache from filesytem ...")

            with open(self.cache_store_path_en, "rb") as f:
                self.resource_map_en = pickle.load(f)

            with open(self.cache_store_path_de, "rb") as f:
                self.resource_map_de = pickle.load(f)

            with open(self.cache_store_path_islands, "rb") as f:
                self.all_islands = pickle.load(f)

            with open(self.cache_store_path_grids, "rb") as f:
                self.all_grids = pickle.load(f)

    # -------------------------------------------------------------------------
    # connect to google sheets (login & obtain token)

    def connect(self):
        self.log.info("Connecting ...")

        # re-authenticate or load credentials from fs

        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                self.credentials = pickle.load(token)

        if not self.credentials or not self.credentials.valid:
            self.log.info("(Re-)authenticating ...")

            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                self.credentials = flow.run_local_server()

            # Save the credentials for the next run
            
            with open(self.token_path, "wb") as token:
                pickle.dump(self.credentials, token)            
        else:
            self.log.info("Reusing existing authentication")

        if self.credentials and self.credentials.valid:
            self.service = build("sheets", "v4", credentials = self.credentials, cache_discovery=False)

        return self.service is not None

    # -------------------------------------------------------------------------
    # (re-)load cache of resources

    def load_cache(self):
        if self.service is None:
            raise RuntimeError("Not connected")

        new_resource_map_en = {}
        new_resource_map_de = {}
        new_all_islands = set()
        new_all_grids = set()

        self.log.info("Updating sheets data cache ...")
        
        # query list of sheets in document
        
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId = self.sheet_id).execute()

        if not sheet_metadata or not sheet_metadata['sheets']:
            self.log.info("Received malformed when querying sheet meta data")
            return False

        sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]

        self.log.info("Found sheets: {}".format(", ".join(sheet_names)))

        # loop grids

        for grid_name in sheet_names:
            if "template" in grid_name.lower():
                continue

            result = self.service.spreadsheets().values().get(spreadsheetId = self.sheet_id, 
                                                                range = grid_name).execute()

            if not result:
                self.log.info("Received malformed when querying sheet data")
                return False
            
            rows = result.get('values', [])

            # loop all rows of the grid.
            # row 1:    title in col 0 and island names in col >0
            # row >1:   resource name in col 0 and True/False in col >0

            for row_num in range(1, len(rows)):
                row = rows[row_num]
                resource_en = None
                resource_de = None

                for col in range(len(row)):
                    if col >= len(rows[0]):
                        break

                    island_name = rows[0][col]

                    # remember the resource we're talking about if this is col 0
                    # also kind of normalize the name

                    if col == 0:
                        resource_en = row[col].split("/")[0].lower().strip()
                        resource_de = row[col].split("/")[-1].lower().strip()

                        if resource_en.endswith("(nodes)"):
                            resource_en = rep.sub('[ ]*\\(nodes\\)', '', resource_en)

                        if resource_de.endswith("ader"):
                            resource_de = rep.sub('ader$', '', resource_de)

                        if resource_en and resource_en not in new_resource_map_en and "(" not in resource_en:
                            new_resource_map_en[resource_en] = { "title": row[col], "info": [] }

                        if resource_de and resource_de not in new_resource_map_de and "(" not in resource_de:
                            new_resource_map_de[resource_de] = { "title": row[col], "info": [] }
                    else:
                        if resource_en == "" or "(" in resource_de or "(" in resource_en:
                            continue

                        # append the location to the global map and the grid info

                        info = { "grid": grid_name[:2], 
                                "island": island_name, 
                                "cell": chr(ord('A')+col) + str(row_num),
                                "avail": row[col] }

                        new_all_islands.add(island_name)
                        new_all_grids.add(grid_name[:2])

                        new_resource_map_en[resource_en]["info"].append(info)
                        new_resource_map_de[resource_de]["info"].append(info)

        # make reloaded lists available

        self.resource_map_en = new_resource_map_en
        self.resource_map_de = new_resource_map_de
        self.all_islands = list(sorted(new_all_islands))
        self.all_grids = list(sorted(new_all_grids))

        # and dump them to the fs for later re-use without re-query

        with open(self.cache_store_path_en, 'wb') as f:
            pickle.dump(self.resource_map_en, f, pickle.HIGHEST_PROTOCOL)

        with open(self.cache_store_path_de, 'wb') as f:
            pickle.dump(self.resource_map_de, f, pickle.HIGHEST_PROTOCOL)

        with open(self.cache_store_path_islands, 'wb') as f:
            pickle.dump(self.all_islands, f, pickle.HIGHEST_PROTOCOL)

        with open(self.cache_store_path_grids, 'wb') as f:
            pickle.dump(self.all_grids, f, pickle.HIGHEST_PROTOCOL)

        self.log.info("Done reloading cache.")

    # -------------------------------------------------------------------------
    # find_resource

    def find_resource(self, search_string, only_grids = False):
        resource_infos = []
        titles = []
        search_string_lower = search_string.lower()

        for key in self.resource_map_en.keys():
            if key in search_string_lower:
                available_at_all = [x for x in self.resource_map_en[key]["info"] if x["avail"] == 'TRUE']
                
                if available_at_all:
                    resource_infos.append(self.resource_map_en[key])

                titles.append(self.resource_map_en[key]["title"])

        for key in self.resource_map_de.keys():
            if key in search_string_lower:
                available_at_all = [x for x in self.resource_map_de[key]["info"] if x["avail"] == 'FALSE']

                if available_at_all:
                    resource_infos.append(self.resource_map_de[key])

                titles.append(self.resource_map_de[key]["title"])

        # found?

        if len(resource_infos) <= 0:
            if len(titles) > 0:
                return { "title": "/".join(titles), "not_yet_in_list": True }

            return None

        # assemble the response string (like : 'A1 (Island1, Island2), A3 (Island1, Island5)')

        found_strings = []
        found_grid_names = []

        for resource_info in resource_infos:
            title = resource_info["title"]
            infos = resource_info["info"]
            found_grids = {}
            res = []

            for island, grid in [(record["island"],record["grid"]) for record in infos if record["avail"] == "TRUE"]:
                if grid not in found_grids:
                    found_grids[grid] = []

                found_grids[grid].append(island)
                found_grid_names.append(grid)

            for found in found_grids.keys():
                res.append(found + " (" +  ", ".join(found_grids[found]) + ")")

            location = ", ".join(res)

            found_strings.append({ "title": title, "location": location })
            
            if not only_grids:
                self.log.info("Found resource '{}' in {}".format(title, location))

        if only_grids:
            return found_grid_names

        return found_strings

    # -------------------------------------------------------------------------
    # find_resource

    def find_resource_by_grid(self, search_string, grid):
        islands = []
        other_grid_islands = []
        title = None

        for key in self.resource_map_en.keys():
            if key in search_string.lower():
                title = self.resource_map_en[key]["title"]

                for info in self.resource_map_en[key]["info"]:
                    if info["grid"] == grid and info["avail"] == "TRUE":
                        islands.append(info["island"])

        for key in self.resource_map_de.keys():
            if key in search_string.lower():
                title = self.resource_map_de[key]["title"]

                for info in self.resource_map_de[key]["info"]:
                    if info["grid"] == grid and info["avail"] == "TRUE":
                        islands.append(info["island"])

        # found?

        if len(islands) <= 0:
            other_grids = self.find_resource(search_string, only_grids = True)
            
            if not other_grids:
                return None

            return { "title": title, "other_grids": list(sorted(set(other_grids))) }

        # return a dict with the full resource title according to resource sheet + list of islands

        return { "title": title, "islands": islands }

    # -------------------------------------------------------------------------
    # contains_keys

    def contains_keys(self, message):

        # check if a given text contains one of the cached resource keys

        for key in self.resource_map_en.keys():
            if key in message:
                return True

        for key in self.resource_map_de.keys():
            if key in message:
                return True

        return False

    # -------------------------------------------------------------------------
    # get_keys

    def get_keys(self):
        return list(sorted(set(list(self.resource_map_en.keys()) + list(self.resource_map_de.keys()))))

    # -------------------------------------------------------------------------
    # get_grids

    def get_grids(self):
        return self.all_grids
    
    # -------------------------------------------------------------------------
    # get_islands

    def get_islands(self):
        return self.all_islands;