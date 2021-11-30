import shutil, psutil
import signal
import os
import asyncio

from pyrogram import idle, filters, types, emoji
from sys import executable
from datetime import datetime
import pytz
import time
import threading

from telegram.error import BadRequest, Unauthorized
from telegram import ParseMode, BotCommand, InputTextMessageContent, InlineQueryResultArticle, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Filters, InlineQueryHandler, MessageHandler, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler
from telegraph import Telegraph
from wserver import start_server_async
from bot import bot, app, dispatcher, updater,  IMAGE_URL, CHANNEL_LINK, SUPPORT_LINK, botStartTime, IGNORE_PENDING_REQUESTS, IS_VPS, PORT, alive, web, OWNER_ID, AUTHORIZED_CHATS, telegraph_token, RESTARTED_GROUP_ID, RESTARTED_GROUP_ID2, TIMEZONE
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper import button_build
from .modules import cancel_mirror, mirror_status, mirror, clone, watch, delete, leech_settings
now=datetime.now(pytz.timezone(f'{TIMEZONE}'))

def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>Bot Uptime:</b> <code>{currentTime}</code>\n' \
            f'<b>Total Disk Space:</b> <code>{total}</code>\n' \
            f'<b>Used:</b> <code>{used}</code> ' \
            f'<b>Free:</b> <code>{free}</code>\n\n' \
            f'<b>Upload:</b> <code>{sent}</code>\n' \
            f'<b>Download:</b> <code>{recv}</code>\n\n' \
            f'<b>CPU:</b> <code>{cpuUsage}%</code> ' \
            f'<b>RAM:</b> <code>{memory}%</code> ' \
            f'<b>DISK:</b> <code>{disk}%</code>'
    sendMessage(stats, context.bot, update)


def start(update, context):
    start_string = f'''
This bot can mirror all your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
    buttons = button_build.ButtonMaker()
    buttons.buildbutton("Channel", f"{https://t.me/BeastCloudOfficial}")
    buttons.buildbutton("Owner", f"{@VijayD0211}")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    uptime = get_readable_time((time.time() - botStartTime))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private" :
            sendMessage(f"Hey I'm Alive 🙂\nSince: <code>{uptime}</code>", context.bot, update)
        else :
            sendMarkup(start_string, context.bot, update, reply_markup)
    else :
        sendMessage(f"Oops! not a Authorized user.", context.bot, update)


def restart(update, context):
    restart_message = sendMessage("🔄️ 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐈𝐍𝐆...", context.bot, update)
    LOGGER.info(f'Restarting The Bot...')
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    alive.terminate()
    process = psutil.Process(web.pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    os.execl(executable, executable, "-m", "bot")

def log(update, context):
    sendLogFile(context.bot, update)


help_string_telegraph = f'''<br>
<b>/{BotCommands.RestartCommand}</b>: Restart the bot
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Start mirroring the link to Google Drive.
<br><br>
<b>/{BotCommands.TarMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the archived (.tar) version of the download
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the archived (.zip) version of the download
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Starts mirroring and if downloaded file is any archive, extracts it to Google Drive
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link]: Start Mirroring using qBittorrent, Use <b>/{BotCommands.QbMirrorCommand} s</b> to select files before downloading
<br><br>
<b>/{BotCommands.QbTarMirrorCommand}</b> [magnet_link]: Start mirroring using qBittorrent and upload the archived (.tar) version of the download
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link]: Start mirroring using qBittorrent and upload the archived (.zip) version of the download
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link]: Starts mirroring using qBittorrent and if downloaded file is any archive, extracts it to Google Drive
<br><br>
<b>/{BotCommands.LeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.TarLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and upload it as (.tar). [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.ZipLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and upload it as (.zip). [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.UnzipLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and if file is any archive, extracts it. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.QbLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link using qBittorrent. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.QbTarLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and upload it as (.tar) using qBittorrent. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.QbZipLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and upload it as (.zip) using qBittorrent. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.QbUnzipLeechCommand}</b>: This command should be used as reply to Magnet link, Torrent link, or Direct link and if file is any archive, extracts it using qBittorrent. [this command will SPAM the chat and send the downloads a seperate files, if there is more than one file, in the specified Torrent]
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url]: Copy file/folder to Google Drive
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file from Google Drive (Only Owner & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl. Click <b>/{BotCommands.WatchCommand}</b> for more help
<br><br>
<b>/{BotCommands.TarWatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl and zip before uploading
<br><br>
<b>/{BotCommands.LeechWatchCommand}</b>: Leech through youtube-dl 
<br><br>
<b>/{BotCommands.LeechTarWatchCommand}</b>: Leech through youtube-dl and tar before uploading 
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b>: Leech through youtube-dl and zip before uploading 
<br><br>
<b>/{BotCommands.LeechSetCommand}</b>: Leech Settings 
<br><br>
<b>/{BotCommands.SetThumbCommand}</b>: Reply to photo to set it as Thumbnail
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Cancel all running tasks
<br><br>
<b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
'''
help = Telegraph(access_token=telegraph_token).create_page(
        title='BeastCloud',
        author_name='Vijay D',
        author_url='@VijayD0211',
        html_content=help_string_telegraph,
    )["path"]

help_string = f'''
Raad Command Below
'''

def bot_help(update, context):
    button = button_build.ButtonMaker()
    button.buildbutton("Available Commands", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)


botcmds = [
        (f'{BotCommands.Mirror1Command}', 'Start Mirroring'),
        (f'{BotCommands.TarMirror1Command}','Start mirroring and upload as .tar'),
        (f'{BotCommands.ZipMirror1Command}','Start mirroring and upload as .zip'),
        (f'{BotCommands.UnzipMirror1Command}','Extract files'),
        (f'{BotCommands.QbMirror1Command}','Start Mirroring using qBittorrent'),
        (f'{BotCommands.QbTarMirror1Command}','Start mirroring and upload as .tar using qb'),
        (f'{BotCommands.QbZipMirror1Command}','Start mirroring and upload as .zip using qb'),
        (f'{BotCommands.QbUnzipMirror1Command}','Extract files using qBitorrent'),
        (f'{BotCommands.Clone1Command}','Copy file/folder to Drive'),
        (f'{BotCommands.LeechSet1Command}','Setting for leech'),
        (f'{BotCommands.SetThumb1Command}','Set thumb'),
        (f'{BotCommands.Leech1Command}','Leech'),
        (f'{BotCommands.TarLeech1Command}','Tar leech'),
        (f'{BotCommands.UnzipLeech1Command}','Unzip leech'),
        (f'{BotCommands.ZipLeech1Command}','Zip leech'),
        (f'{BotCommands.QbLeech1Command}','Qbit leech'),
        (f'{BotCommands.QbTarLeech1Command}','QbitTar leech'),
        (f'{BotCommands.QbUnzipLeech1Command}','QbitUnzip leech'),
        (f'{BotCommands.QbZipLeech1Command}','QbitZip leech'),
        (f'{BotCommands.LeechWatch1Command}','Youtube leech'),
        (f'{BotCommands.LeechTarWatch1Command}','Youtube Tar leech'),
        (f'{BotCommands.LeechZipWatch1Command}','Youtube Zip leech'),
        (f'{BotCommands.Delete1Command}','Delete file from Drive'),
        (f'{BotCommands.Watch1Command}','Mirror Youtube-dl support link'),
        (f'{BotCommands.TarWatch1Command}','Mirror Youtube playlist link as .tar'),
        (f'{BotCommands.ZipWatch1Command}','Mirror Youtube playlist link as .zip'),
        (f'{BotCommands.Cancel1Mirror}','Cancel a task'),
        (f'{BotCommands.CancelAll1Command}','Cancel all tasks'),
        (f'{BotCommands.Status1Command}','Get Mirror Status message'),
        (f'{BotCommands.Stats1Command}','Bot Usage Stats'),
        (f'{BotCommands.Restart1Command}','Restart the bot [owner/sudo only]'),
    ]

def main():
    # Heroku restarted
    GROUP_ID = f'{RESTARTED_GROUP_ID}'
    kie = datetime.now(pytz.timezone(f'{TIMEZONE}'))
    jam = kie.strftime('\n📅 DATE: %d/%m/%Y\n⏲️ TIME: %I:%M%P')
    if GROUP_ID is not None and isinstance(GROUP_ID, str):        
        try:
            dispatcher.bot.sendMessage(f"{GROUP_ID}", f"♻️ 𝐁𝐎𝐓 𝐆𝐎𝐓 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐄𝐃 ♻️\n{jam}\n\n🗺️ TIME ZONE\n{TIMEZONE}\n\n𝙿𝙻𝙴𝙰𝚂𝙴 𝚁𝙴-𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝙰𝙶𝙰𝙸𝙽\n\n#Restarted")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

# Heroku restarted
    GROUP_ID2 = f'{RESTARTED_GROUP_ID2}'
    kie = datetime.now(pytz.timezone(f'{TIMEZONE}'))
    jam = kie.strftime('\n📅 𝘿𝘼𝙏𝙀: %d/%m/%Y\n⏲️ 𝙏𝙄𝙈𝙀: %I:%M%P')
    if GROUP_ID2 is not None and isinstance(GROUP_ID2, str):        
        try:
            dispatcher.bot.sendMessage(f"{GROUP_ID2}", f"♻️ 𝐁𝐎𝐓 𝐆𝐎𝐓 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐄𝐃 ♻️\n{jam}\n\n🗺️ TIME ZONE\n{TIMEZONE}\n\n𝙿𝙻𝙴𝙰𝚂𝙴 𝚁𝙴-𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝙰𝙶𝙰𝙸𝙽\n\n#Restarted")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)
    
    fs_utils.start_cleanup()
    if IS_VPS:
        asyncio.get_event_loop().run_until_complete(start_server_async(PORT))
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    
    bot.set_my_commands(botcmds)
    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("⚠️ If Any optional vars not be filled it will use Defaults vars")
    LOGGER.info("📶 Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
