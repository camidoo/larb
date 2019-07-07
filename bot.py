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
import spacy

# -----------------------------------------------------------------------------
# class DiscordClient
# -----------------------------------------------------------------------------

class DiscordClient(discord.Client):

    #--------------------------------------------------------------------------
    # ctor

    def __init__(self, classifier, sheets, *args, **kwargs):
        discord.Client.__init__(self, *args, **kwargs)

        self.log = logging.getLogger(__name__)
        self.classifier = classifier
        self.sheets = sheets
        #self.nlp = spacy.load("de_core_news_md")
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

        #doc = self.nlp(message.content)
        #sentences = [sent.string.strip() for sent in doc.sents]

        #for sent in sentences:
        for sent in [message.content]:
            res = self.classifier.classify([message.content])

            if res != "chat":
                await self.process_request(res, sent, message.channel)

    #--------------------------------------------------------------------------
    # process_request

    async def process_request(self, type, message, channel):

        # actually process the request, depending on what type was classified

        if type == "find_resource":

            # give locations for one or more resources.
            # e.g. "Wo gibt es Silber?"

            self.log.info("Finding resource via [{}]".format(message))

            res = self.sheets.find_resource(message)

            if res is not None:
                for dict in res:
                    await channel.send(dict["title"] + " gibt es in " + dict["location"])
            else:
                self.log.info("Resource not found")

        elif type == "find_resource_by_grid":

            # give locations for one or more resources in a given grid.
            # e.g. "Gibt es in C3 Zinn?"

            self.log.info("Finding resource by grid via [{}]".format(message))

            grid_name = None

            for grid in self.sheets.get_grids():
                if grid.lower() in message.lower():
                    grid_name = grid
                    break

            if grid_name:
                res = self.sheets.find_resource_by_grid(message, grid_name)

                if res is None:
                    return

                if "other_grids" not in res:
                    await channel.send(res["title"] + " gibt es in " + grid_name + " auf " + ", ".join(res["islands"]))
                else:
                    await channel.send(res["title"] + " gibt es in " + grid_name + " nicht. Aber auf " + ", ".join(res["other_grids"]) + ".")
            else:
                await self.process_request(self, "find_resource", message, channel)

#------------------------------------------------------------------------------
# class Bot
#------------------------------------------------------------------------------

class Bot:

    #--------------------------------------------------------------------------
    # ctor

    def __init__(self, token_file_name, classifier, sheets):
        self.token = ""
        self.client = None
        self.log = logging.getLogger(__name__)
        self.client = DiscordClient(classifier, sheets, status = 'idle')

        try:
            with open(token_file_name) as f:
                self.token = f.readline().strip()
        except Exception as e:
            self.log.error('Failed to open token file ({})'.format(e))

    #--------------------------------------------------------------------------
    # connect

    def connect(self):
        if not self.token:
            self.log.error('No token available, cannot connect!')
        else:
            self.log.info('Connecting to discord using {} ...'.format(discord.__version__))
            self.client.run(self.token)
