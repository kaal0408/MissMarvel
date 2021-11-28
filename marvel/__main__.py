#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.

import datetime
import random
import html
import importlib
import re
import resource
import platform
import sys
import traceback
import wikipedia
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop, Dispatcher
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from marvel import dispatcher, updater, TOKEN, WEBHOOK, OWNER_ID, CERT_PATH, PORT, URL, LOGGER, client
# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from marvel.modules import ALL_MODULES
from marvel.modules.helper_funcs.chat_status import is_user_admin
from marvel.modules.helper_funcs.misc import paginate_modules
from marvel.modules.translations.strings import tld
from marvel.modules.translations.strings import tld_help
from marvel.modules.connection import connected


PM_START_TEXT = """Hey there! My name is Pikachu - I'm here to help you manage your groups! Hit /help to find out more about how to use me to my full potential.
Join my [news channel](https://t.me/PikachuX_logs) to get information on all the latest updates.
If this bot helped you donate somthing any needed person!
"""

HELP_STRINGS = """Hey. Now you are in help section!
I have lots of handy features, such as flood control, a warning system, a note keeping system, and even predetermined replies on certain keywords.

Helpful commands:
- /start: Starts me! You've probably already used this.
- /help: If you are here you already used this!
- /donate: Gives you info on how to support me and my creator.

If you have any bugs or questions on how to use me, have a look at my group head to @TheBotSupports.
 
All commands can either be used with / or !.

And the following:"""#.format(dispatcher.bot.first_name, "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n")

DONATE_STRING = "Okie"

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("marvel.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(chat_id=chat_id,
                                text=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard)



def test(update, context):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(context.match)
    print(update.effective_message.text)


RANDOM_START = (
    "Hey I'm Alive",
    "Hey Whatssup?",
    "Why you awaked meh?",
    "Hello there how can i help you?",
    "Arey you human?",
    "Hey I'm Coded by @Hayat_Murat_30",
    "Are you alive ? Umm I think yes",
    "Are you stalking meh ?",
	"Relax I'm here",
    "I'm Alive what about you? "
)
def start(update, context):
    if update.effective_chat.type == "private":
        args = context.args
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, tld(update.effective_message, HELP_STRINGS))

            
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

            elif args[0][:4] == "wiki":
                wiki = args[0].split("-")[1].replace('_', ' ')
                message = update.effective_message
                getlang = langsql.get_lang(message)
                if getlang == "id":
                    wikipedia.set_lang("id")
                pagewiki = wikipedia.page(wiki)
                judul = pagewiki.title
                summary = pagewiki.summary
                if len(summary) >= 4096:
                    summary = summary[:4000]+"..."
                message.reply_text("<b>{}</b>\n{}".format(judul, summary), parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text=tld(update.effective_message, "Read it on Wikipedia"), url=pagewiki.url)]]))

            
        else:
            first_name = update.effective_user.first_name
            buttons = InlineKeyboardMarkup( 
                [[InlineKeyboardButton(text="🎉 Add Me", url="t.me/Pikachu_x__bot?startgroup=botstart"), InlineKeyboardButton(text="❓ Help", callback_data="help_back")],
                [InlineKeyboardButton(text="👥 Support Group", url="https://t.me/Pikachux_support")],
                
            update.effective_message.reply_text(
                tld(update.effective_message, PM_START_TEXT).format(escape_markdown(first_name), escape_markdown(context.bot.first_name), OWNER_ID),
                disable_web_page_preview=True,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=buttons)

# for test purposes

    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    # devs = [OWNER_ID]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an 
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message 
    # could fail
    # if update.effective_message:
    #   text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
    #         "My developer(s) will be notified."
    #   update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    #  trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    

        




    

    # dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
            client.run_until_disconnected()

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4)
        client.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    client.start(bot_token=TOKEN)
    main()
