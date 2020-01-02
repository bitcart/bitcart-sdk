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
from bitcart import BCH, BSTY, BTC, GZRO, LTC

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
bch = BCH(xpub=XPUB)
ltc = LTC(xpub=XPUB)
gzro = GZRO(xpub=XPUB)
bsty = BSTY(xpub=XPUB)
# same api, so we can do this
instances = {"btc": btc, "bch": bch, "ltc": ltc, "gzro": gzro, "bsty": bsty}
satoshis_hundred = 0.000001

# misc

deposit_select_filter = Filters.create(
    lambda _, cbq: bool(re.match(r"^deposit_", cbq.data))
)
deposit_filter = Filters.create(lambda _, cbq: bool(re.match(r"^pay_", cbq.data)))
bet_filter = Filters.create(lambda _, cbq: bool(re.match(r"^bet_", cbq.data)))
paylink_filter = Filters.create(lambda _, cbq: bool(re.match(r"^pl_", cbq.data)))
paylink_pay_filter = Filters.create(lambda _, cbq: bool(re.match(r"^plp_", cbq.data)))
pagination_filter = Filters.create(lambda _, cbq: bool(re.match(r"^page_", cbq.data)))


class Paginator:
    items_per_page = 10

    def __init__(self, data):
        self.data = data

    def get_page(self, page):
        end = page * self.items_per_page
        start = end - self.items_per_page
        return self.data[start:end]

    def get_starting_count(self, page):
        return ((page - 1) * self.items_per_page) + 1

    def has_next_page(self, page):
        return self.data.count() >= (page * self.items_per_page) + 1

    def has_prev_page(self, page):
        return page > 1


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
        [
            InlineKeyboardButton("Bitcoin (BTC)", callback_data=f"pay_btc_{amount}"),
            InlineKeyboardButton(
                "Bitcoin Cash (BCH)", callback_data=f"pay_bch_{amount}"
            ),
            InlineKeyboardButton("Litecoin (LTC)", callback_data=f"pay_ltc_{amount}"),
        ],
        [
            InlineKeyboardButton("Gravity (GZRO)", callback_data=f"pay_gzro_{amount}"),
            InlineKeyboardButton(
                "GlobalBoost (BSTY)", callback_data=f"pay_bsty_{amount}"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def paylink_kb(currency, amount):
    keyboard = [
        [InlineKeyboardButton("Bot link", callback_data=f"pl_bot_{currency}_{amount}")],
        [
            InlineKeyboardButton(
                "Payment request(for non-bot users)",
                callback_data=f"pl_pr_{currency}_{amount}",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


@app.on_message(Filters.command("help"))
def help_handler(client, message):
    # bitcart: get usd price
    usd_price = round(btc.rate() * satoshis_hundred, 2)
    message.reply(
        f"""
<b>In development, now working commands are tip!xxx, /start, /help, /deposit, /balance, /send, /history, /send2telegram, /paylink, /claim, /bet and /top</b>
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
/bet [currency] 1000 <i>[up|down|same] [minute|hour|day|month] Bet on currencies prices</i>
Betting rewards amounts are based on the time you bet for:
1 % profit if betting for one minute
13 % profit if betting for one hour
19 % profit if betting for one day
23 % profit if betting for one month
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


def get_user_repr(user_id):
    user = app.get_users(user_id)
    return f"{user.first_name}({user.username})"


def paylink_pay_kb(deposit_id, amount):
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"plp_y_{deposit_id}_{amount}")],
        [InlineKeyboardButton("No", callback_data=f"plp_n_{deposit_id}_{amount}")],
    ]
    return InlineKeyboardMarkup(keyboard)


@app.on_message(Filters.command("start"))
def start(client, message):
    # quote=False with reply is just a shorter version of
    # app.send_message(chat_id, message)
    user_id = message.from_user.id
    user = get_user_data(user_id)
    texts = message.text.split()
    # paylink handling
    send_welcome = True
    try:
        if len(texts) == 2:
            deposit_id, amount = texts[1].split("=")
            deposit_id = int(deposit_id)
            amount = int(amount)
            if amount <= 0 or user["balance"] < amount:
                message.reply("Not enough balance to pay the paylink.")
            else:
                if deposit_id != user_id:
                    message.reply(
                        f"Paying paylink with {amount} satoshis to {get_user_repr(deposit_id)}. Proceed?",
                        reply_markup=paylink_pay_kb(deposit_id, amount),
                    )
            send_welcome = False
    except ValueError:
        send_welcome = True
    if send_welcome:
        message.reply(
            "Welcome to the Bitcart Atomic TipBot! /help for list of commands",
            quote=False,
        )


@app.on_callback_query(paylink_pay_filter)
def pay_paylink(client, message):
    user_id = message.from_user.id
    _, answer, deposit_id, amount = message.data.split("_")
    deposit_id = int(deposit_id)
    amount = int(amount)
    if answer == "y":
        change_balance(deposit_id, amount, "paylink")
        change_balance(user_id, -amount, "paylink")
        message.edit_message_text(
            f"Successfully paid the paylink with {amount} satoshis."
        )
        app.send_message(
            deposit_id, f"Your paylink was successfuly paid by {get_user_repr(user_id)}"
        )
    else:
        message.edit_message_text(f"Paylink canceled.")


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


def convert_amounts(currency, amount):
    currency = currency.lower()
    amount /= instances[currency].rate("BTC")
    return amount, instances[currency].friendly_name


def generate_invoice(user_id, currency, amount, amount_sat, description=""):
    amount, friendly_name = convert_amounts(currency, amount)
    # bitcart: create invoice
    invoice = instances[currency].addrequest(
        amount, description, expire=20160
    )  # 14 days
    invoice.update(
        {"user_id": user_id, "currency": currency, "original_amount": amount_sat}
    )
    mongo.invoices.insert_one(invoice)
    return invoice, amount, friendly_name


@app.on_callback_query(deposit_filter)
def deposit_query(client, call):
    call.edit_message_text("Okay, almost done! Now generating invoice...")
    _, currency, amount = call.data.split("_")
    amount_sat = int(amount)
    amount_btc = amount_sat * 0.00000001
    user_id = call.from_user.id
    invoice, amount, _ = generate_invoice(
        user_id, currency, amount_btc, amount_sat, f"{secret_id(user_id)} top-up"
    )
    send_qr(
        invoice["URI"],
        user_id,
        client,
        caption=f"Your invoice for {amount_sat} Satoshi ({amount:0.8f} {currency.upper()}):\n{invoice['address']}",
    )


@app.on_message(Filters.private & Filters.command("paylink"))
def paylink(client, message):
    user_id = message.from_user.id
    try:
        _, currency, amount_sat = message.command
        amount_sat = int(amount_sat)
    except ValueError:
        return message.reply(
            "Invalid amount. Command format to request 1000 satoshi in BTC: /paylink btc 1000"
        )
    message.reply(
        "Which link would you like to get?",
        reply_markup=paylink_kb(currency, amount_sat),
        quote=False,
    )


@app.on_callback_query(paylink_filter)
def paylink_query(client, message):
    user_id = message.from_user.id
    _, link_type, currency, amount_sat = message.data.split("_")
    amount_sat = int(amount_sat)
    amount_btc = amount_sat / 100000000
    amount, currency_name = convert_amounts(currency, amount_btc)
    if link_type == "pr":
        invoice, _, _ = generate_invoice(
            user_id, currency, amount_btc, amount_sat, f"{secret_id(user_id)} paylink"
        )
        invoice_link = invoice["URI"]
    elif link_type == "bot":
        bot_username = app.get_me().username
        invoice_link = f"https://t.me/{bot_username}?start={user_id}={amount_sat}"
    try:
        message.edit_message_text(
            f"Invoice for {amount_sat} Satoshi [{amount:.8f} {currency.upper()}]\n\nMessage to forward:"
        )
        time.sleep(1)
        app.send_message(
            chat_id=user_id,
            text=f"Send me {currency_name.lower()} using this link: {invoice_link}",
        )
    except BadRequest as e:
        pass


# After addition of APIManager this should get even easier
@btc.on("new_payment")
@bch.on("new_payment")
@ltc.on("new_payment")
@gzro.on("new_payment")
@bsty.on("new_payment")
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
        return message.reply("Invalid amount specified", quote=False)
    coin_obj = instances.get(currency.lower())
    if not coin_obj:
        return message.reply("Invalid currency", quote=False)
    user = get_user_data(user_id)
    if amount <= 0 or user["balance"] < amount:
        return message.reply("Not enough balance", quote=False)
    amount_btc = amount / 100000000
    amount_to_send = amount_btc / coin_obj.rate("BTC")
    wallet_balance = float(
        coin_obj.balance()["confirmed"]
    )  # TODO: investigate why it is a string
    if wallet_balance < amount_to_send:
        available_coins = []
        for coin in instances:
            coin_balance = float(instances[coin].balance()["confirmed"])
            if coin_balance >= amount_to_send:
                available_coins.append(instances[coin].coin_name)
        wallet_balance_sat = int(
            round(wallet_balance * coin_obj.rate("BTC") * 100000000, 8)
        )
        return message.reply(
            f'Current {currency} wallet balance: {wallet_balance_sat}. \nIf you want to withdraw {amount} satoshis, you can do so in any of these currencies: {", ".join(available_coins)}',
            quote=False,
        )
    # bitcart: send to address in BTC
    try:
        tx_hash = coin_obj.pay_to(address, amount_to_send)
        # payment succeeded, we have tx hash
        change_balance(user_id, -amount, "withdraw", tx_hash)
        message.reply(f"Successfuly withdrawn. Tx id: {tx_hash}", quote=False)
    except Exception:
        error_line = traceback.format_exc().splitlines()[-1]
        message.reply(f"Error occured: \n<code>{error_line}</code>", quote=False)


def render_history_page(paginator, page):
    count = paginator.get_starting_count(page)
    page_data = paginator.get_page(page)
    msg = ""
    for i in page_data:
        msg += f"{count}. "
        msg += f"{i['amount']} satoshis at {i['date']}."
        if i["tx_hash"]:
            msg += f"\nTx hash: {i['tx_hash']}."
        elif i["address"]:
            msg += f"\nSent to: {i['address']}."
        msg += f" Type: {i['type']}\n"
        count += 1
    return msg


@app.on_message(Filters.private & Filters.command("history"))
def history(client, message):
    query = {"user_id": message.from_user.id}
    msg = "Transaction history:\n"
    markup = None
    if mongo.txes.count_documents(query):
        txes = mongo.txes.find(query)
        paginator = Paginator(txes)
        msg += render_history_page(paginator, 1)
        if paginator.has_next_page(1):
            markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("▶️", callback_data="page_2")]]
            )
    else:
        msg += "Empty"
    message.reply(msg, reply_markup=markup, quote=False)


@app.on_callback_query(pagination_filter)
def history_page(client, message):
    _, page = message.data.split("_")
    page = int(page)
    query = {"user_id": message.from_user.id}
    txes = mongo.txes.find(query)
    paginator = Paginator(txes)
    msg = "Transaction history:\n"
    msg += render_history_page(paginator, page)
    markup = None
    keyboard = []
    if paginator.has_prev_page(page):
        keyboard.append(InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
    if paginator.has_next_page(page):
        keyboard.append(InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
    if keyboard:
        markup = InlineKeyboardMarkup([keyboard])
    message.edit_message_text(msg, reply_markup=markup)


def charge_user(user_id, amount, tx_type="bet"):
    user = get_user_data(user_id)
    if amount > 0 and user["balance"] >= amount:
        change_balance(user_id, -amount, tx_type)
        return True
    else:
        return False


def make_bet(userid, currency, amount, trend, set_time, chat_id, msg_id):
    currency = currency.lower()
    if (
        amount < 1
        or set_time not in ["minute", "hour", "day", "month"]
        or trend not in ["up", "down", "same"]
        or currency not in instances
    ):
        app.send_message(
            chat_id=chat_id,
            text="Wrong command usage. /bet [currency] 1000 <i>[up|down|same] [minute|hour|day|month]</i>",
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

        price = instances[currency].rate("USD")

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
            "currency": currency,
            "amount": amount,
            "win": win_amount,
        }
        mongo.bets.insert_one(bet_data)
        coin_name = instances[currency].coin_name.lower()  # bitcart: get coin data
        app.send_message(
            chat_id=chat_id,
            text=f"Your {amount} sat bet is accepted, hodler! You will receive {win_amount} if {coin_name} price go {trend} from {price:.8f}@Coingecko in a {set_time}",
            reply_to_message_id=msg_id,
        )
        try:
            app.send_animation(
                chat_id=userid, animation=BET_LUCK_IMAGES[trend], caption="Good luck!"
            )
        except BadRequest:
            pass
        return True
    else:
        try:
            app.send_animation(
                userid,
                animation=BET_LUCK_IMAGES["nobalance"],
                caption="Not enought funds. Would you like to top-up? /deposit",
            )
        except BadRequest:
            pass
        return False


@app.on_message(Filters.command("bet"))
def bet(client, message):
    try:
        _, currency, amount, trend, date = message.command
        amount = int(amount)
        make_bet(
            message.from_user.id,
            currency,
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
        "btc",
        3000,
        trend,
        "hour",
        message.message.chat.id,
        message.message.message_id,
    )


def genvoucher(user_id, amount, receiver):
    dtime = datetime.strftime(datetime.now(), DATE_FORMAT)
    voucher = secrets.token_urlsafe(8)
    receiver = receiver.replace("@", "")

    voucher_data = {
        "timestamp": dtime,
        "code": voucher,
        "event": "send2telegram",
        "from": user_id,
        "to": app.resolve_peer(receiver).user_id,
        "to_username": receiver,
        "amount": amount,
    }
    mongo.vouchers.insert_one(voucher_data)
    return voucher


@app.on_message(Filters.command("send2telegram"))
def send2telegram(client, message):
    user_id = message.from_user.id
    try:
        _, receiver, amount = message.command
        amount = int(amount)
        if charge_user(user_id, amount, receiver):
            genvoucher(user_id, amount, receiver)
            message.reply(
                f"Funds reserved for {receiver}, now he needs send /claim command to @bitcart_atomic_tipbot"
            )
        else:
            try:
                app.send_animation(
                    user_id,
                    animation="https://i.imgur.com/UY8I7ow.gif",
                    caption="Not enought funds. Would you like to top-up? /deposit",
                )
            except BadRequest:
                pass
    except ValueError:
        message.reply(
            "Failed to send funds. Command format to send 10000 to @MrNaif_bel: /send2telegram @MrNaif_bel 10000"
        )


@app.on_message(Filters.private & Filters.command("claim"))
def claim(client, message):
    user_id = message.from_user.id
    get_user_data(user_id)
    vouchers = mongo.vouchers.find({"to": user_id})
    count = 0
    sum_ = 0
    for v in vouchers:
        count += 1
        sum_ += v["amount"]
        mongo.vouchers.delete_one({"_id": v["_id"]})
        dtime = datetime.strftime(datetime.now(), DATE_FORMAT)
        v.pop("_id", None)
        v["redeemed"] = dtime
        mongo.voucher_archive.insert_one(v)
    if sum_ > 0:
        change_balance(user_id, sum_, "vouchers")
    message.reply(f"{count} vouchers redeemed for {sum_} satoshi in total")


def betcheck(first=False):
    if first:
        time.sleep(10)
    threading.Timer(30.0, betcheck).start()

    ##check bets
    bets = (
        mongo.bets.find({"status": "new"}).sort("amount", pymongo.DESCENDING).limit(10)
    )

    prices = {
        currency: instances[currency].rate("USD") for currency in instances
    }  # dict comprehension

    for bet in bets:
        now_time = datetime.now()
        bet_exp = bet["unixtime_exp"]
        price = prices[bet["currency"]]
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
                    caption=f"Congratulations! You won {bet['win']} satoshis! {bet['price']:.8f} {bet['trend']} {price:.8f}",
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
                    caption=f"Your bet wasn't lucky one! Bet on {bet['price']:.8f} {bet['trend']}, but price is {price:.8f}",
                )
            mongo.bets.update_one({"_id": bet["_id"]}, {"$set": {"status": "expired"}})
        time.sleep(1)


threading.Thread(target=betcheck, kwargs={"first": True}).start()
# Starting polling for all coins, with APIManager this should get easier
threading.Thread(target=btc.poll_updates).start()  # or .start_webhook()
threading.Thread(target=bch.poll_updates).start()
threading.Thread(target=ltc.poll_updates).start()
threading.Thread(target=gzro.poll_updates).start()
threading.Thread(target=bsty.poll_updates).start()
app.start()
