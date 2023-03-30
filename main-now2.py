#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using nested ConversationHandlers.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

# TODO: крч я до пилил регистрацию обычного юзера до вроде бы без ошибок, закончил тем что сделал зацикленую работу без ошибок
# TODO: 16.03 - РАзобрался с ngrok и сделал тестовую ссылку впервые скооперировал три запуска с локалхоста

from scrip_number_check import sms_check
from config import host, user, password, db_name

import logging
from typing import Any, Dict, Tuple

from telegram import __version__ as TG_VER, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode

import psycopg2
from re import sub, findall
from telegram import __version__ as TG_VER
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
global urlll
global sms_api_id
urlll = 'https://6a55-77-222-114-50.eu.ngrok.io/'
sms_api_id = "DE3CCBFB-4CCF-8A1B-8634-A9759DE0A9C8"

connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
connection.autocommit = True

# State definitions for top level conversation
SELECTING_ACTION, CHECK_DOCTOR, ADDING_MEMBER, ADDING_SELF, DESCRIBING_SELF = map(chr, range(5))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_GENDER, REG_OR_LOG = map(chr, range(5, 8))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING, TYPING_DOCTOR, DOCTOR_PASS, DATA_FILING, SELECTING_FEATURE_CLIENT, TYPING_CLIENT = map(chr,
                                                                                                                  range(
                                                                                                                      8,
                                                                                                                      15))
# Meta states
STOPPING, SHOWING = map(chr, range(15, 17))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    PARENTS,
    CHILDREN,
    CLIENT_REGISTR,
    CLIENT_LOGIN,
    SELF,
    GENDER,
    MALE,
    FEMALE,
    REGISTR,
    LOGIN,
    AGE,
    NAME,
    NUMBER,
    PASSPORT,
    START_OVER_CLIENT,
    CLIENT,
    INFO_CLIENT,
    END_CLIENT,
    START_OVER,
    FEATURES,
    CURRENT_INFO_CLIENT,
    CURRENT_FEATURE,
    CURRENT_LEVEL_CLIENT,
    CURRENT_LEVEL,
) = map(chr, range(17, 41))


# Helper
def _name_switcher(level: str) -> Tuple[str, str]:
    if level == PARENTS:
        return "заполнить данные", "загрузить доккументы"
    return "Brother", "Sister"


def _name_switcher2(level: str) -> Tuple[str, str]:
    if level == CLIENT_REGISTR:
        return "заполнить данные", "загрузить доккументы"
    return "Brotherreee", "Sistererheh"


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    print(context.user_data)
    text = (
        'Привет! \n'
        'Я телеграм бот, который помогает спасти жизни, кто ты из пользователей?;)\n'
    )

    buttons = [
        [
            InlineKeyboardButton(text="Врач", callback_data=str(CHECK_DOCTOR)),
            InlineKeyboardButton(text="НЕ врач", callback_data=str(ADDING_SELF)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need to send a new message
    if context.user_data.get(START_OVER) or context.user_data.get(START_OVER_CLIENT):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        print(context.user_data)
    else:
        print(context.user_data)
        await update.message.reply_text(
            "Hi, I'm Family Bot and I'm here to help you gather information about your family."
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


# ------------------ Вход врача ------------------------


# async def check_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
#     text = 'введи пароль для врачей'
#     await update.callback_query.edit_message_text(text=text)


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Pretty print gathered data."""

    def pretty_print(data: Dict[str, Any], level: str) -> str:
        people = data.get(level)
        if not people:
            return "\nNo information yet."

        return_str = ""
        if level == SELF:
            for person in data[level]:
                return_str += f"\nName: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
        else:
            male, female = _name_switcher(level)

            for person in data[level]:
                gender = female if person[GENDER] == FEMALE else male
                return_str += (
                    f"\n{gender}: Номер: {person.get(NAME, '-')}, Паспорт: {person.get(AGE, '-')}"
                )
        return return_str

    user_data = context.user_data
    text = f"Yourself:{pretty_print(user_data, SELF)}"
    text += f"\n\nParents:{pretty_print(user_data, PARENTS)}"
    text += f"\n\nChildren:{pretty_print(user_data, CHILDREN)}"

    buttons = [[InlineKeyboardButton(text="Back", callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    user_data[START_OVER] = True

    return SHOWING


# Second level conversation callbacks

async def check_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = 'dsf'
    buttons = [
        [
            InlineKeyboardButton(text="Ввести пароль врача", callback_data=str(AGE)),
            InlineKeyboardButton(text="Где взять пароль?", callback_data=str(ADDING_SELF)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return DOCTOR_PASS


async def save_input_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    text = "Okay, tell me."
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)
    return TYPING_DOCTOR


async def save_input_doctor_second(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    if update.message.text == '1234':
        return await select_level(update, context)
    else:
        await  update.message.reply_text(text='WRONG PASSWORD')
        return STOPPING


async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    print('тут я после того как нажал добавить члена семьи')
    text = "You may add a parent or a child. Also you can show the gathered data or go back."
    buttons = [
        [
            InlineKeyboardButton(text="регистрация", callback_data=str(PARENTS)),
            InlineKeyboardButton(text="вход", callback_data=str(CHILDREN)),
        ],
        [
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # await update.callback_query.answer()
    try:
        await update.message.reply_text(text=text, reply_markup=keyboard)
    except AttributeError:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_LEVEL


# ------------------------- конец входа врача ----------------------------------------------

# ------------------------ ветка регистрации клиента----------------------------------------


async def adding_self(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add information about yourself."""
    """Choose to add a parent or a child."""
    text = "You may add a parent or a child. Also you can show the gathered data or go back."
    buttons = [
        [
            InlineKeyboardButton(text="регистрация", callback_data=str(CLIENT_REGISTR)),
            InlineKeyboardButton(text="вход", callback_data=str(CLIENT_LOGIN)),
        ],
        [
            InlineKeyboardButton(text="Back", callback_data=str(END_CLIENT)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return REG_OR_LOG
    # context.user_data[CURRENT_LEVEL] = SELF
    # text = "Okay, please tell me about yourself."
    # button = InlineKeyboardButton(text="Add info", callback_data=str(MALE))
    # keyboard = InlineKeyboardMarkup.from_button(button)
    #
    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # return DESCRIBING_SELF


async def reg_or_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add mother or father."""
    global urlll
    print('тут я после того как нажал добавить родителя')
    level = update.callback_query.data
    print(level, 'reg_or_log')
    context.user_data[CURRENT_LEVEL_CLIENT] = level

    text = "Please choose, whom to add."

    registr, login = _name_switcher2(level)
    log_url = urlll

    buttons = [
        [
            InlineKeyboardButton(text=f"Я зарегистрировался", callback_data=str(REGISTR)),
        ],
        [
            InlineKeyboardButton(text="Back", callback_data=str(END_CLIENT)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    url = 'https://6a55-77-222-114-50.eu.ngrok.io/'

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=f'<a href="{urlll}">Нажми на меня чтобы зарегестрироваться</a>\n'
                                                       f'После регистриации нажми на кнопку',
                                                  parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                                                  reply_markup=keyboard)

    return SELECTING_FEATURE_CLIENT


# Third level callbacks
# async def data_filing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
#     """Select a feature to update for the person."""
#     print('сюда попал после того как нажал добавить отца')
#
#     buttons = [
#         [
#             InlineKeyboardButton(text="Номер телефона", callback_data=str(NUMBER)),
#             InlineKeyboardButton(text="Паспорт", callback_data=str(PASSPORT)),
#             InlineKeyboardButton(text="Done", callback_data=str(END_CLIENT)),
#         ]
#     ]
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     # await update.message.reply_text(
#     #     "Please press the button below to choose a color via the WebApp.",
#     #     reply_markup=ReplyKeyboardMarkup.from_button(
#     #         KeyboardButton(
#     #             text="Open the color picker!",
#     #             request_contact=True
#     #         )
#     #     ),
#     # )
#
#
#
#     # If we collect features for a new person, clear the cache and save the gender
#     if not context.user_data.get(START_OVER_CLIENT):
#         context.user_data[INFO_CLIENT] = {CLIENT: update.callback_query.data}
#         text = "Отправь свой номер телефона для потверждения"
#
#         await update.callback_query.answer()
#         await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#     # But after we do that, we need to send a new message
#     else:
#         text = "Отправь свой номер телефона для потверждения"
#         await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     context.user_data[START_OVER_CLIENT] = False
#     return SELECTING_FEATURE_CLIENT


async def ask_for_input_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_INFO_CLIENT] = update.callback_query.data
    text = "Отправь свой номер телефона для потверждения"

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING_CLIENT


async def save_input_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    global sms_api_id
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    # user_data[INFO_CLIENT][user_data[CURRENT_INFO_CLIENT]] = update.message.text

    # user_data[START_OVER_CLIENT] = True
    st = update.message.text
    number = ''
    if len(st) != '':
        norm_mob = sub(r'(\s+)?[+]?', '', st)
        # проверяем строку на наличие в ней только необходимых символов
        right_mob = findall(r'[\d]', norm_mob)
        # если количество знаков в двух строках совпадает, значит это номер телефона
        if (len(right_mob) == len(norm_mob)) and (len(norm_mob) >= 11):
            rev_norm_mob = norm_mob[::-1]
            norm_mob = rev_norm_mob[0:11]
            if norm_mob[::-1][0] == '7' or norm_mob[::-1][0] == '8':
                number = norm_mob[::-1]
                number = '7' + number[1::]
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT EXISTS (SELECT * FROM users WHERE number =%s );""",
                        (number,)
                    )
                    if cursor.fetchone():
                        print('she s got it')
                        sms = sms_check(sms_api_id)
                        send_sms_result = sms.send(f"{number}", "1234")
                        await update.message.reply_text(text=f'{send_sms_result}')

                    else:
                        text = 'Пользователя с таким номером телефона не найдено, убедитесь, что вы регистрировались ' \
                               'по ссылке. '
                        await update.message.reply_text(text=text)

    if not number:
        text = 'Невернно введен номер'
        await update.message.reply_text(text=text)

    # return await data_filing(update, context)


async def end_describing_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL_CLIENT]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[INFO_CLIENT])

    # Print upper level menu
    if level == SELF:
        user_data[START_OVER_CLIENT] = True
        await start(update, context)
    else:
        await adding_self(update, context)

    return END_CLIENT


async def end_second_level_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER_CLIENT] = True
    await start(update, context)

    return END_CLIENT


# ------------------конец ветки регистрации клиента---------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")

    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END


async def select_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add mother or father."""
    print('тут я после того как нажал добавить родителя')
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = "Please choose, whom to add."

    male, female = _name_switcher(level)

    buttons = [
        [
            InlineKeyboardButton(text=f"Add {male}", callback_data=str(MALE)),
            InlineKeyboardButton(text=f"Add {female}", callback_data=str(FEMALE)),
        ],
        [
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_GENDER


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


# Third level callbacks
async def select_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select a feature to update for the person."""
    print('сюда попал после того как нажал добавить отца')

    buttons = [
        [
            InlineKeyboardButton(text="Номер телефона", callback_data=str(NAME)),
            InlineKeyboardButton(text="Паспорт", callback_data=str(AGE)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = "Please select a feature to update."

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = "Got it! Please select a feature to update."
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = "Okay, tell me."

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING


async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text
    print(user_data[FEATURES][user_data[CURRENT_FEATURE]])
    print(FEATURES)
    print(CURRENT_FEATURE)

    user_data[START_OVER] = True

    return await select_feature(update, context)


async def end_describing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[FEATURES])

    # Print upper level menu
    if level == SELF:
        user_data[START_OVER] = True
        await start(update, context)
    else:
        await select_level(update, context)

    return END


async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Completely end conversation from within nested conversation."""
    await update.message.reply_text("Okay, bye.")

    return STOPPING


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("1533304329:AAHVhvmtXETWT4eDJrjzmbMn7Ac1XScSbwM").build()

    # Set up third level ConversationHandler (collecting features)
    description_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                select_feature, pattern="^" + str(MALE) + "$|^" + str(FEMALE) + "$"
            )
        ],
        states={
            SELECTING_FEATURE: [
                CallbackQueryHandler(ask_for_input, pattern="^(?!" + str(END) + ").*$")
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )
    # Set up third level ConversationHandler (collecting features)
    description_client_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ask_for_input_client, pattern="^" + str(REGISTR) + "$|^" + str(LOGIN) + "$")

        ],
        states={
            # SELECTING_FEATURE_CLIENT: [
            #     CallbackQueryHandler(ask_for_input_client, pattern="^(?!" + str(END_CLIENT) + ").*$")
            # ],
            TYPING_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input_client)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing_client, pattern="^" + str(END_CLIENT) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # Return to second level menu
            END_CLIENT: REG_OR_LOG,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    # Set up second level ConversationHandler (adding a person)
    add_member_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_doctor, pattern="^" + str(CHECK_DOCTOR) + "$")],
        states={
            DOCTOR_PASS: [
                CallbackQueryHandler(save_input_doctor, pattern="^(?!" + str(END) + ").*$")
            ],
            TYPING_DOCTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input_doctor_second)],
            ADDING_MEMBER: [CallbackQueryHandler(select_level, pattern="^" + str(ADDING_MEMBER) + "$")],
            SELECTING_LEVEL: [
                CallbackQueryHandler(select_gender, pattern=f"^{PARENTS}$|^{CHILDREN}$")
            ],
            SELECTING_GENDER: [description_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
            CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation altogether
            STOPPING: END,
        },
    )

    add_client_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adding_self, pattern="^" + str(ADDING_SELF) + "$"), ],
        states={
            REG_OR_LOG: [
                CallbackQueryHandler(reg_or_log, pattern=f"^{CLIENT_REGISTR}$|^{CLIENT_LOGIN}$")
            ],
            SELECTING_FEATURE_CLIENT: [description_client_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
            CallbackQueryHandler(end_second_level_client, pattern="^" + str(END_CLIENT) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END_CLIENT: SELECTING_ACTION,
            # End conversation altogether
            STOPPING: END_CLIENT,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        add_member_conv,
        add_client_conv,
        CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),  # регулярное выражение
        CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
        CallbackQueryHandler(end, pattern="^" + str(END_CLIENT) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: selection_handlers,
            SELECTING_LEVEL: selection_handlers,
            DESCRIBING_SELF: [description_conv],
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
