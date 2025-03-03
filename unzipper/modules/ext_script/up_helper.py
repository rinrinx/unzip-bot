# Copyright (c) 2023 EDM115
import os
import pathlib
import re
import shutil
import subprocess
from asyncio import sleep
from time import time

from pyrogram.errors import FloodWait

from config import Config
from unzipper import LOGGER
from unzipper import unzipperbot
from unzipper.helpers.database import get_upload_mode
from unzipper.helpers.unzip_help import extentions_list
from unzipper.helpers.unzip_help import progress_for_pyrogram
from unzipper.modules.bot_data import Messages
from unzipper.modules.ext_script.custom_thumbnail import thumb_exists


# To get video duration and thumbnail
async def run_shell_cmds(command):
    run = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    shell_output = run.stdout.read()[:-1].decode("utf-8").rstrip('\n')
    LOGGER.info(shell_output)
    if run.stderr:
        run.stderr.close()
    if run.stdout:
        run.stdout.close()
    return shell_output

disabled = """
async def run_shell_command(command, timeout=None):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        raise Exception(f"Command '{command}' timed out after {timeout} seconds")

    if process.returncode != 0:
        raise Exception(f"Command '{command}' failed with error code {process.returncode}: {stderr.decode().strip()}")

    return stdout.decode().strip()
"""


# Get file size
async def get_size(doc_f):
    try:
        fsize = os.stat(doc_f).st_size
        return fsize
    except:
        return -1


# Send file to a user
async def send_file(unzip_bot, c_id, doc_f, query, full_path, log_msg, split):
    fsize = await get_size(doc_f)
    if fsize == -1:  # File not found
        try:
            await unzip_bot.send_message(c_id, Messages.EMPTY_FILE.format(os.path.basename(doc_f)))
        except:
            pass
        return
    if fsize == 0:  # Empty file
        try:
            await unzip_bot.send_message(c_id, Messages.EMPTY_FILE.format(os.path.basename(doc_f)))
        except:
            pass
        return
    try:
        ul_mode = await get_upload_mode(c_id)
        fname = os.path.basename(doc_f)
        fext = ((pathlib.Path(os.path.abspath(doc_f)).suffix).casefold().replace(".", ""))
        thumbornot = await thumb_exists(c_id)
        upmsg = await unzip_bot.send_message(c_id, Messages.PROCESSING2)
        if ul_mode == "media" and fext in extentions_list["audio"]:
            if thumbornot:
                thumb_image = Config.THUMB_LOCATION + "/" + str(c_id) + ".jpg"
                await unzip_bot.send_audio(
                    chat_id=c_id,
                    audio=doc_f,
                    caption=Messages.EXT_CAPTION.format(fname),
                    thumb=thumb_image,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
            else:
                await unzip_bot.send_audio(
                    chat_id=c_id,
                    audio=doc_f,
                    caption=Messages.EXT_CAPTION.format(fname),
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
        elif ul_mode == "media" and fext in extentions_list["photo"]:
            # impossible to use a thumb here :(
            await unzip_bot.send_photo(
                chat_id=c_id,
                photo=doc_f,
                caption=Messages.EXT_CAPTION.format(fname),
                progress=progress_for_pyrogram,
                progress_args=(
                    Messages.TRY_UP.format(fname),
                    upmsg,
                    time(),
                    unzip_bot,
                ),
            )
        elif ul_mode == "media" and fext in extentions_list["video"]:
            vid_duration = await run_shell_cmds(
                f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {doc_f}"
            )
            if thumbornot:
                thumb_image = Config.THUMB_LOCATION + "/" + str(c_id) + ".jpg"
                await unzip_bot.send_video(
                    chat_id=c_id,
                    video=doc_f,
                    caption=Messages.EXT_CAPTION.format(fname),
                    duration=int(vid_duration) if vid_duration.isnumeric() else 0,
                    thumb=thumb_image,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
            else:
                thmb_pth = (
                    f"{Config.THUMB_LOCATION}/thumbnail_{os.path.basename(doc_f)}.jpg"
                )
                if os.path.exists(thmb_pth):
                    os.remove(thmb_pth)
                try:
                    await run_shell_cmds(
                        f"ffmpeg -ss 00:00:01.00 -i {doc_f} -vf 'scale=320:320:force_original_aspect_ratio=decrease' -vframes 1 {thmb_pth}"
                    )
                except Exception as e:
                    LOGGER.warning(e)
                    shutil.copyfile(Config.BOT_THUMB, thmb_pth)
                await unzip_bot.send_video(
                    chat_id=c_id,
                    video=doc_f,
                    caption=Messages.EXT_CAPTION.format(fname),
                    duration=int(vid_duration) if vid_duration.isnumeric() else 0,
                    thumb=str(thmb_pth),
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
                os.remove(thmb_pth)
        else:
            if thumbornot:
                thumb_image = Config.THUMB_LOCATION + "/" + str(c_id) + ".jpg"
                await unzip_bot.send_document(
                    chat_id=c_id,
                    document=doc_f,
                    thumb=thumb_image,
                    caption=Messages.EXT_CAPTION.format(fname),
                    force_document=True,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
            else:
                await unzip_bot.send_document(
                    chat_id=c_id,
                    document=doc_f,
                    caption=Messages.EXT_CAPTION.format(fname),
                    force_document=True,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Messages.TRY_UP.format(fname),
                        upmsg,
                        time(),
                        unzip_bot,
                    ),
                )
        await upmsg.delete()
        os.remove(doc_f)
    except FloodWait as f:
        await sleep(f.value)
        return await send_file(unzip_bot, c_id, doc_f, query, full_path, log_msg, split)
    except FileNotFoundError:
        try:
            await unzip_bot.send_message(c_id, Messages.CANT_FIND.format(os.path.basename(doc_f)))
        except:
            pass
        return
    except BaseException as e:
        LOGGER.warning(e)
        shutil.rmtree(full_path)


async def send_url_logs(unzip_bot, c_id, doc_f, source):
    try:
        u_file_size = os.stat(doc_f).st_size
        if Config.TG_MAX_SIZE < int(u_file_size):
            await unzip_bot.send_message(
                chat_id=c_id, text=Messages.TOO_LARGE
            )
            return
        fname = os.path.basename(doc_f)
        await unzip_bot.send_document(
            chat_id=c_id,
            document=doc_f,
            caption=Messages.LOG_CAPTION.format(fname, source),
        )
    except FloodWait as f:
        await sleep(f.value)
        return send_url_logs(unzip_bot, c_id, doc_f, source)
    except FileNotFoundError:
        await unzip_bot.send_message(
            chat_id=Config.LOGS_CHANNEL,
            text=Messages.ARCHIVE_GONE,
        )
    except BaseException:
        pass


async def merge_splitted_archives(user_id, path):
    cmd = f"cd {path} && cat * > MERGED_{user_id}.zip"
    await run_shell_cmds(cmd)


# Function to remove basic markdown characters from a string
async def rm_mark_chars(text: str):
    return re.sub("[*`_]", "", text)


# Function to answer queries
async def answer_query(
    query, message_text: str, answer_only: bool = False, unzip_client=None, buttons=None
):
    try:
        if answer_only:
            await query.answer(await rm_mark_chars(message_text), show_alert=True)
        else:
            await query.message.edit(message_text, reply_markup=buttons)
    except:
        try:
            if unzip_client:
                await unzip_client.send_message(
                    chat_id=query.message.chat.id, text=message_text, reply_markup=buttons
                )
            else:
                await unzipperbot.send_message(
                    chat_id=query.message.chat.id, text=message_text, reply_markup=buttons
                )
        except:
            pass
