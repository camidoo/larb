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

import logging
import sys
import sheets
import dataset

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# parseArgs
#------------------------------------------------------------------------------

def parseArgs():
    def _getArg(a):
        try:
            res = a.split('=', 2)

            if len(res) == 1:
                return res[0].replace('--', ''), None
            else:
                return res
        except Exception as e: 
            print("LOL {}", e)
            return None

    return { kv[0]: kv[1] for kv in list(map(_getArg, sys.argv)) if kv != None }

# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

# google sheets login:
# python.sheets.test710@gmail.com
# pw: Batman5.

def main(args):
    sheet_id = "1qYD1u48jWug6CS_Fyy2OXgIIWTu2sMXmxUzfUCC_fwU"  # radioactive atlas
    # sheet_id = "1Tu-kMkRgixJ2NInHSds0rJAHxYqD7hV84u8UbzQuZkI"   # dummy  / dev

    shts = sheets.SheetsCache(cache_store_dir = "./cache", 
                                credentials_path = "./security/credentials.json", 
                                token_path = "./security/token.pickle", 
                                sheet_id = sheet_id)

    # if not shts.connect():
    #     log.error("Failed to connect to google sheets")
    #     return -1

    # shts.load_cache()
    #print(shts.find_resource("Weiß jemand wo ich Saps finde?"))
    #print(shts.find_resource_by_grid("Gibt es in C3 Zinn?", "C3"))

    all_grids = shts.get_grids() 
    all_keys = shts.get_keys()

    ds = dataset.Dataset(data_dir = "./data", 
                        sources = [
                        # ("train_chat.txt", "chat", None), 
                        ("train_resource.txt", "find_resource", { "#resource#": all_keys }),
                        ("train_verification_samples.txt", "chat", None), 
                        ("train_resource_by_grid.txt", "find_resource", { "#grid#": all_grids })
                        ])

    clsf = classifier.ChatClassifier(model_save_dir = "./model", dataset = ds)

    #print(clsf.classify(["Wo gibts auf D4 silber?", "Wo kann ich Affen finden?", "Gibt es irgendwo Holz?", "Auf welcher Insel gibt es Silber?"]))

    # with open("./data/big_chat_cleaned.txt") as my_file:
    #     for line in my_file:
    #         message = line[:-1]

    #         res = clsf.classify([message])

    #         if "chat" not in res and len(message) > 15:
    #             print("[{}] in [{}]".format(res, message))

    # for key in shts.get_keys():
    #     checks = [
    #                 "Wo gibt es {}?".format(key), 
    #                 "Wo finde ich {}?".format(key), 
    #                 "Auf welcher Insel gibt es {}?".format(key), 
    #                 "Sagtmal wo gibt es {}?".format(key),
    #                 "wer weiß wos {} gibt?".format(key),
    #                 "wer weis wos {} hat?".format(key)
    #             ]

    #     for check in checks:
    #         res = clsf.classify([check])

    #         if "find_resource" not in res:
    #             print("[" + check + "] + -> " + res[0])

    discbot = bot.Bot("./security/token.txt", clsf, shts)
    discbot.connect()

#------------------------------------------------------------------------------
# run
#------------------------------------------------------------------------------

if __name__ == '__main__':
    args = parseArgs()

    if 'console' in args:
        logger.Logger.static_init(None)
    else:
        logger.Logger.static_init("bot.log")

    main(args)