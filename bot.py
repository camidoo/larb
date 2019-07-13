# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# bot.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import discord
import re as rep

# -----------------------------------------------------------------------------
# class DiscordClient
# -----------------------------------------------------------------------------

class DiscordClient(discord.Client):

    #--------------------------------------------------------------------------
    # ctor

    def __init__(self, nlp, classifier, sheets, *args, **kwargs):
        discord.Client.__init__(self, *args, **kwargs)

        self.log = logging.getLogger(__name__)
        self.classifier = classifier
        self.sheets = sheets
        self.nlp = nlp
        self.username = None

    #--------------------------------------------------------------------------
    # on_ready

    async def on_ready(self):
        self.username = self.user.name
        self.log.info('Logged on as {}'.format(self.username))

    #--------------------------------------------------------------------------
    # on_message

    async def on_message(self, message):
        # don't respond to ourselves

        if message.author == self.user:
            return

        # use spacy / NLP to split a block of text into separate sentences.
        # then process sentence by sentence

        doc = self.nlp(message.content)
        sentences = [sent.string.strip() for sent in doc.sents]

        for sent in sentences:
            # use ML classifier to determine whether or not this sentence is a request for resource location

            try:
                res = self.classifier.classify([sent])

                # if so, process it further

                if res and res[0] != "chat":
                    response = self.process_request(res, sent)

                    if response is None:
                        return

                    for response_msg in response:
                        await message.channel.send(response_msg)
            except Exception as e:
                self.log.error("Failed to process chat ({})".format(e))

    #--------------------------------------------------------------------------
    # process_request

    def process_request(self, type, message):
        requested_grid = None

        # actually process the request, depending on what type was classified
        # currently, only "find_resource" can be a valid query.

        if type == "find_resource":
            msg_lower = message.lower()
            contains_key = False

            # (1) check if indeed the sentence contains a valid resource key.

            for key in self.sheets.get_keys():
                if key.lower() in msg_lower:
                    contains_key = True
                    break

            if not contains_key:
                return None

            # (2) if a valid island name is contained in the sentence ("Wo auf Teneriffa gibts Holz?")
            #     skip the request, as we cannot give locations on islands

            for island in self.sheets.get_islands():
                if island.lower() in msg_lower:
                    return None

            # (3) if a valid grid name is found in the message ("Wo in C2 gibts Holz?")
            #     do a "find_resource_by_grid" query, otherwise plain "find_resource" query

            for grid in self.sheets.get_grids():
                grid_match = rep.search("[^a-zA-Z0-9]" + grid.lower() + "([^a-zA-Z0-9]|$)", msg_lower)
                
                if grid_match is not None:
                    requested_grid = grid
                    break

            if requested_grid is not None:
                # (4a) give locations for one or more resources in a given grid.
                #      e.g. "Gibt es in C3 Zinn?"

                self.log.debug("Finding resource by grid via [{}]".format(message))

                res = self.sheets.find_resource_by_grid(message, requested_grid)

                if res is None:
                    self.log.debug("Resource not found")
                    return None

                if "not_yet_in_list" in res:
                    return [res["title"] + " hat noch niemand in die Resourcenliste eingetragen :/"]
                
                if "other_grids" not in res:
                    return [res["title"] + " gibt es in " + requested_grid + " auf " + ", ".join(res["islands"])]

                return [res["title"] + " gibt es in " + requested_grid + " nicht. Aber auf " + ", ".join(res["other_grids"]) + "."]
            else:
                # (4b) give locations for one or more resources without grid information.
                #      e.g. "Wo gibt es Silber?"

                self.log.debug("Finding resource via [{}]".format(message))

                res = self.sheets.find_resource(message)

                if res is None:
                    self.log.debug("Resource not found")
                    return None

                if "not_yet_in_list" in res:
                    return [res["title"] + " hat noch niemand in die Resourcenliste eingetragen :/"]
                
                return [dict["title"] + " gibt es in " + dict["location"] for dict in res]
        else:
            self.log.warning("Got request for unknown classification '{}', ignoring!".format(type))

#------------------------------------------------------------------------------
# class Bot
#------------------------------------------------------------------------------

class Bot:

    #--------------------------------------------------------------------------
    # ctor

    def __init__(self, token_file_name, nlp, classifier, sheets):
        self.token = ""
        self.client = None
        self.log = logging.getLogger(__name__)
        self.client = DiscordClient(nlp, classifier, sheets, status = 'idle')

        try:
            with open(token_file_name) as f:
                self.token = f.readline().strip()
        except Exception as e:
            self.log.error('Failed to open token file ({})'.format(e))

    #--------------------------------------------------------------------------
    # connect

    async def connect(self):
        if not self.token:
            self.log.error('No token available, cannot connect!')
        else:
            self.log.info('Connecting to discord using discord.py v{} ...'.format(discord.__version__))
            await self.client.start(self.token)

    #--------------------------------------------------------------------------
    # disconnect

    async def disconnect(self):
        await self.client.logout()
