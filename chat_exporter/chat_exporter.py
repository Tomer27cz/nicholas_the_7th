import datetime
import io
from typing import List, Optional

from chat_exporter.construct.transcript import Transcript
from chat_exporter.ext.discord_import import discord
from chat_exporter.construct.attachment_handler import AttachmentHandler, AttachmentToLocalFileHostHandler, AttachmentToDiscordChannelHandler

async def raw_export(
    channel: discord.TextChannel,
    messages: List[discord.Message],
    tz_info="UTC",
    guild: Optional[discord.Guild] = None,
    bot: Optional[discord.Client] = None,
    military_time: Optional[bool] = False,
    fancy_times: Optional[bool] = True,
    attachment_handler: Optional[AttachmentHandler] = None,
):
    """
    Create a customised transcript with your own captured Discord messages
    This function will return the transcript which you can then turn in to a file to post wherever.
    :param channel: discord.TextChannel - channel to Export
    :param messages: List[discord.Message] - list of Discord messages to export
    :param tz_info: (optional) TZ Database Name - set the timezone of your transcript
    :param guild: (optional) discord.Guild - solution for edpy
    :param bot: (optional) discord.Client - set getting member role colour
    :param military_time: (optional) boolean - set military time (24hour clock)
    :param fancy_times: (optional) boolean - set javascript around time display
    :param attachment_handler: (optional) AttachmentHandler - allows custom asset handling
    :return: string - transcript file make up
    """
    if guild:
        channel.guild = guild

    return (
        await Transcript(
            channel=channel,
            limit=None,
            messages=messages,
            pytz_timezone=tz_info,
            military_time=military_time,
            fancy_times=fancy_times,
            before=None,
            after=None,
            bot=bot,
            attachment_handler=attachment_handler
        ).export()
    ).html


