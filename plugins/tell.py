"""
tell.py
Created By:
    - CloudBot IRC <https://github.com/ClodbotIRC>
Modified By:
    - Josh Elsasser <https://github.com/jaelsasser>

License:
    GNU General Public License (Version 3)
"""
# TODO: true case-insensitve matching

import re
from datetime import datetime
from sqlalchemy import Table, Column, String, Boolean, DateTime

from sqlalchemy.sql import select

from cloudbot import hook
from cloudbot.util import timeformat, database
from cloudbot.event import EventType

table = Table(
    'hfy-tells',
    database.metadata,
    Column('connection', String(25)),
    Column('channel', String(25, collation='NOCASE')),
    Column('sender', String(25, collation='NOCASE')),
    Column('target', String(25, collation='NOCASE')),
    Column('message', String(500)),
    Column('is_read', Boolean),
    Column('time_sent', DateTime),
    Column('time_read', DateTime),
    extend_existing=True
)


@hook.on_start
def load_cache(db):
    """
    :type db: sqlalchemy.orm.Session
    """
    global tell_cache
    tell_cache = []
    for row in db.execute(table.select().where(table.c.is_read == 0)):
        conn = row["connection"]
        target = row["target"]
        tell_cache.append((conn, target))


def get_unread(db, server, target, channel='*'):
    clauses = [table.c.channel == '*', table.c.channel == channel.lower()]
    query = select([table.c.sender, table.c.channel, table.c.message, table.c.time_sent]) \
        .where(table.c.connection == server.lower()) \
        .where((table.c.channel == '*') | (table.c.channel == channel.lower())) \
        .where(table.c.target == target) \
        .where(table.c.is_read == 0) \
        .order_by(table.c.time_sent)
    return db.execute(query).fetchall()


def count_unread(db, server, target):
    query = select([table]) \
        .where(table.c.connection == server.lower()) \
        .where(table.c.target == target) \
        .where(table.c.is_read == 0) \
        .alias("count") \
        .count()
    return db.execute(query).fetchone()[0]


def read_tell(db, server, channel, target, message):
    query = table.update() \
        .where(table.c.connection == server.lower()) \
        .where(table.c.channel == channel.lower()) \
        .where(table.c.target == target) \
        .where(table.c.message == message) \
        .values(is_read=1)
    db.execute(query)
    db.commit()
    load_cache(db)


def add_tell(db, server, channel, sender, target, message):
    query = table.insert().values(
        connection=server.lower(),
        channel=channel.lower(),
        sender=sender,
        target=target,
        message=message,
        is_read=False,
        time_sent=datetime.today()
    )
    db.execute(query)
    db.commit()
    load_cache(db)


def tell_check(conn, nick):
    for _conn, _target in tell_cache:
        if (conn, nick.lower()) == (_conn, _target.lower()):
            return True


@hook.event([EventType.message, EventType.action], singlethread=True)
def tell_watch(event, conn, db, chan, nick, message, ctcp, reply):
    """
    :type event: cloudbot.event.Event
    :type conn: cloudbot.client.Client
    :type db: sqlalchemy.orm.Session
    """
    if tell_check(conn.name, nick):
        tells = get_unread(db, conn.name, nick, chan)
    else:
        return

    sent = 0
    ratelimit = 5
    for _from, _channel, _message, _sent in tells:
        # format the send time
        reltime = timeformat.time_since(_sent, simple=True, count=1)
        if reltime == 0:
            reltime = "just now"
        else:
            reltime += " ago"

        out = "{}: [{}, {}] {}".format(nick, _from, reltime, _message)
        read_tell(db, conn.name, _channel, nick, _message)

        if sent < ratelimit:
            message(out)
        else:
            if sent == ratelimit + 1:
                reply("{} more tells sent privately.".format(len(tells) - sent))
            ctcp(out)
        sent += 1


@hook.command("tell")
def tell_cmd(text, nick, db, notice, conn, chan):
    """tell <nick> <message> -- Relay <message> to <nick> when <nick> is around."""
    query = text.split(' ', 1)

    if len(query) != 2:
        notice(conn.config("command_prefix") + tell_cmd.__doc__)
        return

    target = query[0]
    message = query[1].strip()
    sender = nick

    if target.lower() == sender.lower():
        notice("Bad user. Bad. Stop trying to .tell yourself")
        return

    # we can't send messages to ourselves
    if target.lower() == conn.nick.lower():
        notice("Invalid nick '{}'.".format(target))
        return

    if not re.match("^[a-z0-9_|.\-\]\[]*$", target.lower()):
        notice("Invalid nick '{}'.".format(target))
        return

    # tells received via PM can be received anywhere
    if chan.lower() == nick.lower():
        chan = '*'

    if count_unread(db, conn.name, target) >= 25:
        notice("What, you trying to kill someone? {} has too many messages queued already.".format(target))
        return

    add_tell(db, conn.name, chan, sender, target, message)
    notice("I'll pass that on when {} is around.".format(target))
