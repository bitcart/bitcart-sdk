import configparser
import os
import re
import secrets
import threading
import time
import traceback
from datetime import datetime, timedelta
from os import getenv

import pymongo
import qrcode
import qrcode.image.svg
import requests
from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest
from pyrogram.session import Session

# BTC class for BTC coin, the same for others, just replace the name
# for litecoin just import LTC
from bitcart import BTC, GZRO, LTC

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
BET_LUCK_IMAGES = {
    "up": "https://i.imgur.com/AcItxdr.gif",
    "down": "https://i.imgur.com/wJYyCSw.gif",
    "same": "https://i.imgur.com/VbC8kNM.gif",
    "nobalance": "https://i.imgur.com/UY8I7ow.gif",
}

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
gzro = GZRO(xpub=XPUB)
# same api, so we can do this
instances = {"btc": btc, "ltc": ltc, "gzro": gzro}
satoshis_hundred = 0.000001

# misc

deposit_select_filter = Filters.create(
    lambda _, cbq: bool(re.match(r"^deposit_", cbq.data))
)
deposit_filter = Filters.create(lambda _, cbq: bool(re.match(r"^pay_", cbq.data)))
bet_filter = Filters.create(lambda _, cbq: bool(re.match(r"^bet_", cbq.data)))


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


def change_balance(user_id, amount, tx_type, tx_hash=None, address=None):
    mongo.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
    mongo.txes.insert_one(
        {
            "user_id": user_id,
            "amount": amount,
            "type": tx_type,
            "tx_hash": tx_hash,
            "address": address,
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


def bet_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Go up!", callback_data="bet_up")],
        [InlineKeyboardButton("Go down!", callback_data="bet_down")],
        [InlineKeyboardButton("Will stay same", callback_data="bet_same")],
    ]
    return InlineKeyboardMarkup(keyboard)


def payment_method_kb(amount):
    keyboard = [
        [InlineKeyboardButton("Bitcoin (BTC)", callback_data=f"pay_btc_{amount}")],
        [InlineKeyboardButton("Litecoin (LTC)", callback_data=f"pay_ltc_{amount}")],
        [InlineKeyboardButton("Gravity (GZRO)", callback_data=f"pay_gzro_{amount}")],
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
    invoice.update(
        {"user_id": userid, "currency": currency, "original_amount": amount_sat}
    )
    mongo.invoices.insert_one(invoice)
    send_qr(
        invoice["URI"],
        userid,
        client,
        caption=f"Your invoice for {amount_sat} Satoshi ({amount:0.8f} {currency.upper()}):\n{invoice['address']}",
    )


# After addition of APIManager this should get even easier
@btc.on("new_payment")
@ltc.on("new_payment")
@gzro.on("new_payment")
def payment_handler(event, address, status, status_str):
    inv = (
        mongo.invoices.find({"address": address}).limit(1).sort([("$natural", -1)])[0]
    )  # to get latest result
    if inv and inv["status"] != "Paid":
        # bitcart: get invoice info, not neccesary here
        # btc.getrequest(address)
        if status_str == "Paid":
            user = mongo.users.find_one({"user_id": inv["user_id"]})
            amount = inv["original_amount"]
            new_balance = user["balance"] + amount
            mongo.invoices.update_one(
                {"address": address}, {"$set": {"status": "Paid"}}
            )
            change_balance(inv["user_id"], amount, "deposit", address=address)
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
Send me currency, address and amount(in satoshis) to send to, separated via space, like so:
btc 181AUpDVRQ3JVcb9wYLzKz2C8Rdb5mDeH7 500
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
        caption=f"You sent {amount} satoshis to {receiver_name}({receiver_username})",
    )
    try:
        app.send_animation(
            reply_id,
            "https://i.imgur.com/U7VL2CV.gif",
            caption=f"You received {amount} satoshis",
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
    coin_obj = instances.get(currency.lower())
    if not coin_obj:
        message.reply("Invalid currency", quote=False)
        return
    user = get_user_data(user_id)
    if amount <= 0 or user["balance"] < amount:
        message.reply("Not enough balance", quote=False)
        return
    amount_btc = amount / 100000000
    amount_to_send = amount_btc / coin_obj.rate("BTC")
    # bitcart: send to address in BTC
    try:
        tx_hash = coin_obj.pay_to(address, amount_to_send)
        # payment succeeded, we have tx hash
        change_balance(user_id, -amount, "withdraw", tx_hash)
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
            msg += f"{i['amount']} satoshis at {i['date']}."
            if i["tx_hash"]:
                msg += f"\nTx hash: {i['tx_hash']}."
            elif i["address"]:
                msg += f"\nSent to: {i['address']}."
            msg += f" Type: {i['type']}\n"
            count += 1
    else:
        msg += "Empty"
    message.reply(msg, quote=False)


def charge_user(user_id, amount, tx_type="bet"):
    user = get_user_data(user_id)
    if amount > 0 and user["balance"] >= amount:
        change_balance(user_id, -amount, tx_type)
        return True
    else:
        return False


def make_bet(userid, amount, trend, set_time, chat_id, msg_id):
    if (
        amount < 1
        or set_time not in ["minute", "hour", "day", "month"]
        and trend not in ["up", "down", "same"]
    ):
        app.send_message(
            chat_id=chat_id,
            text="Wrong command usage. /bet 1000 <i>[up|down|same] [minute|hour|day|month]</i>",
            parse_mode="html",
        )
        return False

    if charge_user(userid, amount, f"bet_{trend}_{set_time}"):
        dtime = datetime.strftime(datetime.now(), DATE_FORMAT)
        if set_time == "minute":
            coef = 1.01
            tdelta = timedelta(minutes=1)
        elif set_time == "hour":
            coef = 1.13
            tdelta = timedelta(hours=1)
        elif set_time == "day":
            coef = 1.19
            tdelta = timedelta(days=1)
        elif set_time == "month":
            coef = 1.23
            tdelta = timedelta(days=30)

        win_amount = int(round(amount * coef))

        price_get = requests.get("https://www.bitstamp.net/api/v2/ticker/btcusd")
        if price_get.status_code == 200:
            price = int(round(float(price_get.json()["last"])))
        else:
            app.send_message(
                chat_id=userid,
                text="error occured getting rate @ bitstamp, try again later",
            )
            return False

        recorddate = datetime.strptime(dtime, DATE_FORMAT)

        unixtime_exp = recorddate + tdelta

        bet_data = {
            "timestamp": dtime,
            "exp_timestamp": datetime.strftime(unixtime_exp, DATE_FORMAT),
            "unixtime_exp": unixtime_exp,
            "event": "bet",
            "chat_id": chat_id,
            "msg_id": msg_id,
            "trend": trend,
            "price": price,
            "status": "new",
            "timeout": set_time,
            "userid": userid,
            "to": "bet_" + trend + "_" + set_time,
            "amount": amount,
            "win": win_amount,
        }
        mongo.bets.insert_one(bet_data)

        app.send_message(
            chat_id=chat_id,
            text=f"Your {amount} sat bet is accepted, hodler! You will receive {win_amount} if bitcoin price go {trend} from {price}@Bitstamp in a {set_time}",
            reply_to_message_id=msg_id,
        )

        app.send_animation(
            chat_id=userid, animation=BET_LUCK_IMAGES[trend], caption="Good luck!"
        )
        return True
    else:
        app.send_animation(
            userid,
            animation=BET_LUCK_IMAGES["nobalance"],
            caption="Not enought funds. Would you like to top-up? /deposit",
        )
        return False


@app.on_message(Filters.command("bet"))
def bet(client, message):
    try:
        _, amount, trend, date = message.command
        amount = int(amount)
        make_bet(
            message.from_user.id,
            amount,
            trend,
            date,
            message.chat.id,
            message.message_id,
        )
    except ValueError:
        message.reply(
            "Bet 3000 satoshi that in a hour Bitcoin price will:",
            reply_markup=bet_menu_keyboard(),
            quote=False,
        )


@app.on_callback_query(bet_filter)
def bet_menu(client, message):
    trend = message.data.split("_")[-1]
    return make_bet(
        message.from_user.id,
        3000,
        trend,
        "hour",
        message.message.chat.id,
        message.message.message_id,
    )


def betcheck(first=False):
    if first:
        time.sleep(10)
    threading.Timer(30.0, betcheck).start()

    ##check bets
    bets = (
        mongo.bets.find({"status": "new"}).sort("amount", pymongo.DESCENDING).limit(10)
    )

    gotprice = False
    price_get = requests.get("https://www.bitstamp.net/api/v2/ticker/btcusd")
    retry = 0
    while not gotprice:
        retry += 1
        if price_get.status_code == 200:
            gotprice = True
            price = int(round(float(price_get.json()["last"])))
        else:
            print(
                f"betcheck: Could not retrieve data from exchange, re-trying: {retry}"
            )

    for bet in bets:
        now_time = datetime.now()
        bet_exp = bet["unixtime_exp"]

        if bet_exp < now_time:
            if bet["trend"] == "up":
                win = bet["price"] < price
            elif bet["trend"] == "down":
                win = bet["price"] > price
            else:
                win = bet["price"] == price
            if win:
                change_balance(bet["userid"], bet["win"], "bet win")
                app.send_animation(
                    chat_id=bet["userid"],
                    animation="https://i.imgur.com/bZAS9ac.gif",
                    caption=f"Congratulations! You won {bet['win']} satoshis! {bet['price']} {bet['trend']} {price}",
                )
                app.send_message(
                    chat_id=bet["chat_id"],
                    text=f'Someone just won {bet["win"]} satoshis on bets!',
                    reply_to_message_id=bet["msg_id"],
                )
            else:
                app.send_animation(
                    chat_id=bet["userid"],
                    animation="https://i.imgur.com/2bmpZsM.gif",
                    caption=f"Your bet wasn't lucky one! Bet on {bet['price']} {bet['trend']}, but price is {price}",
                )
            mongo.bets.update_one({"_id": bet["_id"]}, {"$set": {"status": "expired"}})
        time.sleep(1)


threading.Thread(target=betcheck, kwargs={"first": True}).start()
# Starting polling for all coins, with APIManager this should get easier
threading.Thread(target=btc.poll_updates).start()  # or .start_webhook()
threading.Thread(target=ltc.poll_updates).start()
threading.Thread(target=gzro.poll_updates).start()
app.start()
