import configparser
import os
import re
import secrets
import traceback
from datetime import datetime
from os import getenv

import pymongo
import qrcode
import qrcode.image.svg
from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest
from pyrogram.session import Session

# BTC class for BTC coin, the same for others, just replace the name
# for litecoin just import LTC
from bitcart import BTC, LTC, GZRO

# Don't show message
Session.notice_displayed = True

# load token from config
main_config = configparser.ConfigParser()
main_config.read("config.ini")
try:
    config = main_config["app"]
except KeyError:
    raise ValueError("No [app] section found, exiting...")

# constants
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# loading variables
TOKEN = config.get("token")
XPUB = config.get("xpub")
if not TOKEN:
    raise ValueError(
        "No token provided. Provide it using token variable in [app] section"
    )
if not XPUB:
    raise ValueError("Provide your x/y/z pub/prv in xpub setting in [app] section")

app = Client("tg", bot_token=TOKEN)
mongo = pymongo.MongoClient()
mongo = mongo["atomic_tip_db"]
# bitcart: initialize btc instance
btc = BTC(xpub=XPUB)
# the same here
ltc = LTC(xpub=XPUB)
gzro = GZRO(xpub=config.get("gzro_xpub"))
# same api, so we can do this
instances = {"btc": btc, "ltc": ltc, "gzro": gzro}
satoshis_hundred = 0.000001

# misc

deposit_select_filter = Filters.create(
    lambda _, cbq: bool(re.match(r"^deposit_", cbq.data))
)
deposit_filter = Filters.create(lambda _, cbq: bool(re.match(r"^pay_", cbq.data)))


def get_user_data(user_id):
    user = mongo.users.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "balance": 0,
            "created_time": datetime.now().strftime(DATE_FORMAT),
        }
        mongo.users.insert_one(user)
    return user


def change_balance(user_id, amount, tx_type, tx_hash=None):
    mongo.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
    mongo.txes.insert_one(
        {
            "user_id": user_id,
            "amount": abs(amount),
            "type": tx_type,
            "tx_hash": tx_hash,
            "date": datetime.now().strftime(DATE_FORMAT),
        }
    )


def deposit_keyboard():
    keyboard = [
        [InlineKeyboardButton("100 Satoshi", callback_data="deposit_100")],
        [InlineKeyboardButton("1 000 Satoshi", callback_data="deposit_1000")],
        [InlineKeyboardButton("10 000 Satoshi", callback_data="deposit_10000")],
        [InlineKeyboardButton("100 000 Satoshi", callback_data="deposit_100000")],
    ]
    return InlineKeyboardMarkup(keyboard)


def payment_method_kb(amount):
    keyboard = [
        [InlineKeyboardButton("Bitcoin", callback_data=f"pay_btc_{amount}")],
        [InlineKeyboardButton("Litecoin", callback_data=f"pay_ltc_{amount}")],
        [InlineKeyboardButton("Gravity", callback_data=f"pay_gzro_{amount}")],
    ]
    return InlineKeyboardMarkup(keyboard)


@app.on_message(Filters.command("help"))
def help_handler(client, message):
    # bitcart: get usd price
    usd_price = round(btc.rate() * satoshis_hundred, 2)
    message.reply(
        f"""
<b>In development, now working commands are tip!xxx, /start, /help, /deposit, /balance, /send, /history and /top</b>
<b>Send tip in a group chat:</b>
reply any user message in group including <b>tip!xxx</b> - where xxx is amount you wish to send.
<b>Wallet commands:</b>
/deposit for top-ups
/send to withdraw
/balance to check your balance
/history show transaction history

<b>LApps:</b>
/send2phone +118767854 1000 <i>send satoshi to number by sat2.io</i>
/send2telegram @username 1000 <i> send satoshis to known telegram user</i>
/paylink 10000 <i>request payment link for sharing</i>
/bet 1000 <i>[up|down|same] [minute|hour|day|month] Bet on BTC price</i>
/sendsms +118767854 hello, lightning! <i>send text message to number via lnsms.world</i>

<b>Misc:</b>
/top show user rank

<b>What is 'satoshi'?</b>
<a href=\"https://en.wikipedia.org/wiki/Satoshi_Nakamoto\">Satoshi</a> is a creator of Bitcoin and <a href=\"https://en.bitcoin.it/wiki/Satoshi_(unit)\">currently the smallest unit of the bitcoin currency</a>. Price of 1000 satoshis now is about ${usd_price} (USD)

<b>Have a problem or suggestion?</b>
<a href=\"https://t.me/joinchat/B9nfbhWuDDPTPUcagWAm1g\">Contact bot community</a>"
        """,
        quote=False,
    )


@app.on_message(Filters.command("start"))
def start(client, message):
    # quote=False with reply is just a shorter version of
    # app.send_message(chat_id, message)
    get_user_data(message.from_user.id)
    message.reply(
        "Welcome to the Bitcart Atomic TipBot! /help for list of commands", quote=False
    )


@app.on_message(Filters.command("balance"))
def balance(client, message):
    user_data = get_user_data(message.from_user.id)
    message.reply(f"Your balance is {user_data['balance']} satoshis")


@app.on_message(Filters.command("deposit") & Filters.private)
def deposit(client, message):
    message.reply(
        "Choose amount you want to deposit:",
        reply_markup=deposit_keyboard(),
        quote=False,
    )


# callback query


def send_qr(text, chat_id, client, caption=None):
    file_name = f"files/{secrets.token_urlsafe(32)}.png"
    with open(file_name, "wb") as f:
        qrcode.make("hi").save(f)
    client.send_photo(chat_id, file_name, caption=caption)
    os.remove(file_name)


@app.on_callback_query(deposit_select_filter)
def deposit_select_query(client, call):
    amount = int(call.data[8:])
    call.edit_message_text(
        "Select payment method:", reply_markup=payment_method_kb(amount)
    )


@app.on_callback_query(deposit_filter)
def deposit_query(client, call):
    call.edit_message_text("Okay, almost done! Now generating invoice...")
    _, currency, amount = call.data.split("_")
    amount_sat = int(amount)
    amount_btc = amount_sat * 0.00000001
    userid = call.from_user.id
    if currency == "btc":
        amount = amount_btc
    elif currency == "ltc":
        amount = amount_btc / ltc.rate("BTC")
    elif currency == "gzro":
        amount = amount_btc / gzro.rate("BTC")
    # bitcart: create invoice
    invoice = instances[currency].addrequest(amount, f"{userid} top-up")
    invoice.update({"user_id": userid, "currency": currency})
    mongo.invoices.insert_one(invoice)
    send_qr(
        invoice["URI"],
        userid,
        client,
        caption=f"Your invoice for {amount_sat} Satoshi ({amount:0.8f} {currency.upper()}):\n{invoice['address']}",
    )


@btc.on("new_payment")
def payment_handler(event, address, status, status_str):
    print(address)
    print(status)
    print(status_str)
    inv = mongo.invoices.find_one({"address": i["address"]})
    if inv and inv["status"] != "Paid":
        # bitcart: get invoice info, probably not neccesary here, you can
        # just mark it as paid, but statuses may change in other ways too
        req = btc.getrequest(i["address"])
        if req["status"] == "Paid":
            user = mongo.users.find_one({"user_id": inv["user_id"]})
            amount = req["amount"]
            new_balance = user["balance"] + amount
            mongo.invoices.update_one(
                {"address": i["address"]}, {"$set": {"status": "Paid"}}
            )
            change_balance(
                inv["user_id"], amount, "deposit", i["txes"][0]["tx_hash"]
            )
            app.send_message(
                user["user_id"],
                f"{amount} Satoshis added to your balance. Your balance: {new_balance}",
            )


def secret_id(user_id):
    user_id = str(user_id)
    return f"{user_id[:3]}-{user_id[-3:]}"


@app.on_message(Filters.command("top"))
def top(client, message):
    userlist = mongo.users.find().sort("balance", pymongo.DESCENDING).limit(10)
    balance = get_user_data(message.from_user.id)["balance"]
    msg = "Top 10 users:\n\n"
    place = 1
    for user in userlist:
        if user["balance"] > 0:
            user_id = secret_id(user["user_id"])
            msg_one = f"{place}. {user_id}: {user['balance']}"
            if place <= 3:
                msg_one = f"<b>{msg_one}</b>"
            msg_one += "\n"
            msg += msg_one
            place += 1
    user_id = secret_id(message.from_user.id)
    msg += f"Your ({user_id}) balance: {balance}"
    message.reply(msg, quote=False)


@app.on_message(Filters.private & Filters.command("send"))
def send(client, message):
    message.reply(
        """
Send me bitcoin address and amount(in satoshis) to send to, separated via space, like so:
181AUpDVRQ3JVcb9wYLzKz2C8Rdb5mDeH7 500
""",
        quote=False,
    )


@app.on_message(Filters.reply & Filters.regex(r"[Tt]ip!([0-9]+)"))
def tip(client, message):
    reply_id = message.reply_to_message.from_user.id
    user_id = message.from_user.id
    if reply_id == user_id:
        return
    try:
        amount = int(message.matches[0].group(1))
    except ValueError:
        return
    sender = get_user_data(user_id)
    get_user_data(reply_id)
    receiver_name = message.reply_to_message.from_user.first_name
    receiver_username = message.reply_to_message.from_user.username or "-"
    if amount <= 0 or sender["balance"] < amount:
        return
    change_balance(reply_id, amount, "tip")
    change_balance(user_id, -amount, "tip")
    app.send_animation(
        user_id,
        "https://i.imgur.com/CCqdiZZ.gif",
        f"You sent {amount} satoshis to {receiver_name}({receiver_username})",
    )
    try:
        app.send_animation(
            reply_id,
            "https://i.imgur.com/U7VL2CV.gif",
            f"You received {amount} satoshis",
        )
    except BadRequest:
        pass


@app.on_message(Filters.private & Filters.text & Filters.regex(r"(\w+) (\w+) (\d+)"))
def withdraw(client, message):
    user_id = message.from_user.id
    currency = message.matches[0].group(1)
    address = message.matches[0].group(2)
    try:
        amount = int(message.matches[0].group(3))
    except ValueError:
        message.reply("Invalid amount specified", quote=False)
        return
    print(currency, address, amount)
    user = get_user_data(user_id)
    if amount <= 0 or user["balance"] < amount:
        message.reply("Not enough balance", quote=False)
        return
    amount_btc = amount / 100000000
    # bitcart: send to address in BTC
    try:
        tx_hash = btc.pay_to(address, amount_btc)
        # payment succeeded, we have tx hash
        change_balance(user_id, -amount, "tip", tx_hash)
        message.reply(f"Successfuly withdrawn. Tx id: {tx_hash}", quote=False)
    except Exception:
        error_line = traceback.format_exc().splitlines()[-1]
        message.reply(f"Error occured: \n<code>{error_line}</code>", quote=False)


@app.on_message(Filters.private & Filters.command("history"))
def history(client, message):
    query = {"user_id": message.from_user.id}
    msg = "Transaction history:\n"
    if mongo.txes.count_documents(query):
        txes = mongo.txes.find(query)
        count = 1
        for i in txes:
            msg += f"{count}. "
            sign = "+" if i["type"] == "deposit" else "-"
            msg += f"{sign}{i['amount']} satoshis at {i['date']}."
            if i["tx_hash"]:
                msg += f"Tx hash: {i['tx_hash']}."
            msg += f" Type: {i['type']}\n"
            count += 1
    else:
        msg += "Empty"
    message.reply(msg, quote=False)


with app:
    btc.poll_updates()
