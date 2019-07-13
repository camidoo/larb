'''
-------------------------------------------------------------------------------
logger.py
-------------------------------------------------------------------------------
discord bot v1.0.0
'''

import logging

class Logger:
    def static_init(file_name, level = logging.INFO):
        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
        logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
        
        logging.getLogger('discord.gateway').setLevel(logging.WARNING)
        logging.getLogger('discord.client').setLevel(logging.ERROR)

        if file_name == None:
            logging.basicConfig(level = level, 
                                format = '%(asctime)s:%(name)s:%(levelname)s: %(message)s')
        else:            
            logging.basicConfig(filename = file_name, 
                                level = level, 
                                format = '%(asctime)s:%(name)s:%(levelname)s: %(message)s')