#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# main.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import bot
import logger
import classifier
import sheets
import dataset

import asyncio
import logging
import sys
import signal

import spacy

__version__ = "1.0.0"

#------------------------------------------------------------------------------
# globals
#------------------------------------------------------------------------------

log = logging.getLogger("main")
discbot = None
shts = None

#------------------------------------------------------------------------------
# parseArgs
#------------------------------------------------------------------------------

def parseArgs():
    def _getArg(a):
        try:
            res = a.split('=', 2)

            if len(res) == 1:
                return res[0].replace('--', ''), None

            return res[0].replace('--', ''), res[1]
        except Exception as e: 
            print("Error parsing arguments {}".format(e))
            return None

    return { kv[0]: kv[1] for kv in list(map(_getArg, sys.argv)) if kv != None }

# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

async def main(args):
    global discbot
    global shts

    try:
        sheet_id = args["sheet-id"]
        cache_store_dir = args["cache-dir"]
        sheets_token_path = args["sheets-token-path"]
        sheets_credentials = args["sheets-credentials"]
        discord_token = args["discord-token"]
    except Exception as e:
        log.error("Missing mandatory argument: {}".format(e))
        return

    refresh_time = 600

    if "refresh-time" in args:
        try:
            refresh_time = int(args["refresh-time"])
        except Exception as e:
            pass

    # load NLP module

    nlp_module = "de_core_news_sm" #de_core_news_sm

    log.info("Loading NLP module '{}' ...".format(nlp_module))

    nlp = spacy.load(nlp_module) 

    log.info("Done.")

    # create sheets instance (separate background thread, self-reloading)

    shts = sheets.SheetsCache(cache_store_dir, sheets_credentials, 
                              sheets_token_path, sheet_id, refresh_time = refresh_time)

    shts.start()

    # initialize classifier

    clsf = classifier.ChatClassifier(model_save_dir = "./model", dataset = dataset.Dataset(data_dir = "", sources = []))

    # finally create the discord bot

    discbot = bot.Bot(discord_token, nlp, clsf, shts)

    await discbot.connect()  # blocks

#------------------------------------------------------------------------------
# test
#------------------------------------------------------------------------------

def test():
    print(clsf.classify(["Wo gibts auf D4 silber?", "Wo kann ich Affen finden?", "Gibt es irgendwo Holz?", "Auf welcher Insel gibt es Silber?"]))

    print(shts.find_resource("Weiß jemand wo ich Saps finde?"))
    print(shts.find_resource_by_grid("Gibt es in C3 Zinn?", "C3"))

    with open("./data/big_chat_cleaned.txt") as my_file:
        for line in my_file:
            message = line[:-1]

            res = clsf.classify([message])

            if "chat" not in res and len(message) > 15:
                print("[{}] in [{}]".format(res, message))

    for key in shts.get_keys():
        checks = [
                    "Wo gibt es {}?".format(key), 
                    "Wo finde ich {}?".format(key), 
                    "Auf welcher Insel gibt es {}?".format(key), 
                    "Sagtmal wo gibt es {}?".format(key),
                    "wer weiß wos {} gibt?".format(key),
                    "wer weis wos {} hat?".format(key)
                ]

        for check in checks:
            res = clsf.classify([check])

            if "find_resource" not in res:
                print("[" + check + "] + -> " + res[0])    

#------------------------------------------------------------------------------
# test
#------------------------------------------------------------------------------

def train():
    try:
        sheet_id = args["sheet-id"]
        cache_store_dir = args["cache-dir"]
        sheets_token_path = args["sheets-token-path"]
        sheets_credentials = args["sheets-credentials"]
    except Exception as e:
        log.error("Missing mandatory argument: {}".format(e))
        return

    shts = sheets.SheetsCache(cache_store_dir, sheets_credentials, 
                              sheets_token_path, sheet_id, refresh_time = 60)

    shts.connect()
    shts.reload_cache()

    ds = dataset.Dataset(data_dir = "./data", 
                        sources = [
                        # ("train_chat.txt", "chat", None), 
                        ("train_resource.txt", "find_resource", { "#resource#": shts.get_keys() }),
                        ("train_verification_samples.txt", "chat", None), 
                        ("train_resource_by_grid.txt", "find_resource", { "#grid#": shts.get_grids()  })
                        ])

    clsf = classifier.ChatClassifier(model_save_dir = "./model", dataset = ds, do_train = True)

#------------------------------------------------------------------------------
# test
#------------------------------------------------------------------------------

def help():
    print("LARB - little atlas resource bot version {}".format(__version__))
    print("\nUsage:")
    print("   $ larb [OPTIONS]")
    print("\nOptions:")
    print("   --sheet-id=[ID]               Sets the google sheets ID to [ID]. This ID will be used to query resource data.")
    print("   --sheets-token-path=[PATH]    Storage path for google sheets access tokens.")
    print("   --sheets-credentials=[FILE]   Location of the google sheets credentials file.")
    print("\n   --discord-token=[FILE]        Location of a file containing the discord bot access token.")
    print("\n   --cache-dir=[PATH]            Storage path for cached resources.")
    print("   --refresh-time=[TIME]         Interval in seconds after which the resource cache shall be reloaded from google sheets. Default is 600.")
        

    print("\n   --train                    (Re-)train the ML model for the chat classifier.")
    print("   --help                     Show this help and exit")
    print("   --console                  Log to stdout instead of a dedicated logfile")

    print("\nAll options except train/help/console/refresh-time are MANDATORY.")
    print("\n")

#------------------------------------------------------------------------------
# sigterm_handler
#------------------------------------------------------------------------------

async def sigterm_handler(loop):
    log.info("Shutting down")
    shts.stop()
    await discbot.disconnect()

#------------------------------------------------------------------------------
# run
#------------------------------------------------------------------------------

if __name__ == '__main__':
    args = parseArgs()

    if 'train' in args:
        train()
    elif 'help' in args:
        help()
    else:
        if 'console' in args:
            logger.Logger.static_init(None)
        else:
            log_file = "larb.log"

            if "log-file" in args:
                log_file = args["log-file"]

            logger.Logger.static_init(log_file)

        log.info("Starting LARB v{}".format(__version__))

        loop = asyncio.get_event_loop()
        
        loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(sigterm_handler(loop)))

        try:
            loop.run_until_complete(main(args))
        except KeyboardInterrupt:
            log.info("Shutting down")
            shts.stop()
            loop.run_until_complete(discbot.disconnect())
