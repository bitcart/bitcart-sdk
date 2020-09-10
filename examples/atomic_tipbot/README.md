# Full example of using BitcartCC: Telegram Atomic Tip Bot

The bot is available in telegram at @bitcart_atomic_tipbot

Used tools:
 - Python 3.6+
 - Mongo DB
 - Pyrogram(for bot)
 - qrcode library for generating qr codes
 - BitcartCC to do all the bitcoin and lightning job.

Special thanks to @reablaz, for his original [Atomic tips bot](https://github.com/reablaz/atomic_tipbot)
This bot is rewritten in my style, using modern python 3.6+ f-strings, and of course, BitcartCC. (and made this example reproducible)

## Installation

To get started, you will need to have [Python 3.6+](https://python.org) installed, of course. Using virtualenv is recommended.
Install Mongo DB using it's installation [guide](https://docs.mongodb.com/manual/administration/install-community)
After that, install dependencies of this example using:

`pip install -r requirements.txt`

Check requirements.txt if you want to know exactly which dependencies were used and why.
BitcartCC SDK in pip is just `bitcart`.

After that, to run your bot, you need to have a telegram account, login to
my.telegram.org, click on API development tools, create app if not yet, and take App api_id and api_hash from there.
Don't disclose it to anyone.

Open config.ini.example and replace api_id and api_hash with your own values.
Why is it needed? Because we use Pyrogram, library for developing telegram clients. We can log in as bot, too, and we bypass
HTTP bot api.
Next, go to @BotFather in telegram, and send him /newbot, he will ask you for bot name and username, insert it.
After it is done, copy bot token, and replace token config.ini.example with your token.
After that, you need to get your x/y/z pub/prv(or Electrum seed). Get it from your wallet.
Enter it in xpub section of config.
After that, rename config.ini.example to config.ini.

Now everything is ready, we only need to start BitcartCC daemon.
There are two ways to do it, automatic(via docker, recommended), or directly via your installed python.

### Automatic

Clone bitcart-docker repository:

```
git clone https://github.com/bitcartcc/bitcart-docker
cd bitcart-docker
```

Now you need to configure BitcartCC, but if you need only BTC daemon, run those

```
export BITCART_INSTALL=none
export BITCART_REVERSEPROXY=none
```

If you also need to add lightning, run

`export BTC_LIGHTNING=true`

If you need to run BTC daemon(or others, just replace BTC with coin name) in testnet, also run:

`export BTC_NETWORK=testnet`

After that, run `./setup.sh` to configure and start daemons.

If you will later need to stop them, run `./stop.sh`

### Manual way

As for this example, Python 3.6+ is required. Using virtualenv is recommended.

Clone BitcartCC repository:

```
git clone https://github.com/bitcartcc/bitcart
cd bitcart
```

Install base dependencies:

`pip install -r requirements/base.txt`

To install dependencies for BTC daemon, run:

`pip install -r requirements/daemons/btc.txt`

(If you want to run other daemons, better do that in separate virtualenv)

To run daemon, use:

`python3 daemons/btc.py`

If you need to run daemon in testnet, use:

`BTC_NETWORK=testnet python3 daemons/btc.py`


After that, you can run the bot using `python3 bot.py` and enjoy it!
If you have come here to see how it works, read the next part.

## Reading code

Code is formatted using black, checked with flake8.
Below are some comments regarding what is what.

### BitcartCC

BitcartCC is main in this example, it is used for all bot functions(generate invoice, wait for invoice payment, withdraw, etc.)

[BitcartCC Python SDK](https://pypi.org/project/bitcart) is used to make BitcartCC usage easy. It internally connects to BitcartCC daemon.

Look at # bitcart: comments in code to find things related to BitcartCC.
As you can see, it is quite simple, but let's recap it.

To use any coins you need, simply import them from `bitcart`, in case of bitcoin:

`from bitcart import BTC`

To start using it, we need to initialize BTC class, like so:

`btc = BTC(xpub="your x/y/z pub/prv")`

You can initialize it without any parameters, too, but it will be limited(wallet capabilities not available), and it will produce a warning.

BTC class accepts the following parameters:

 - rpc_url - url of BitcartCC daemon to connect to
 - rpc_user - user to login into your BitcartCC daemon
 - rpc_pass - password to login into your BitcartCC daemon
 - xpub - actually it is not just xpub, it can be x/y/z pub/prv, almost anything. Electrum seed can be used too.
 - session - completely optional, pass your precreated aiohttp.ClientSession(only if you need to customize something in default session)


After intializing coin, you can start using it.
BitcartCC SDK coins' main methods are fully documented(often with examples)
Those are highlevel methods.
If you see something missing, open issue at [BitcartCC SDK repository](https://github.com/bitcartcc/bitcart-sdk)
If you need to use electrum's RPC methods, call them via btc.server(a wrapper around it), like:

`btc.server.validateaddress()`

Pass parameters if any, passing via keyword arguments is possible, but it is **NOT** possible to mix both keyword and
positional arguments.
To see a list of all RPC methods, call

`btc.help()` (internally it calls `btc.server.help()`)

RPC methods accessible via btc.server can't have intellisence in your IDE because they are completely dynamic(via `__getattr__`).

Now, about using BitcartCC in this bot's code.
To get price of 1 bitcoin in USD, simply call `btc.rate()`
Use `btc.add_request(amount, description="", expire=15)` to create BTC invoice
Amount is amount in BTC, description is optional and is description of invoice, expire is the time invoice will expire in, 
default 15 minutes, but if you pass None, invoice will never expire.
This method returns data about newly created invoice:

```
>>> btc.add_request(0.5, "My invoice description", 20)

{'time': 1564678098, 'amount': 1000000, 'exp': 1200, 'address': 'msS5WjurQ6AeKyAM3xHrsB4r1ACiLimoDx', 'memo': 'My invoice description', 'id': 'd46f26f3a8', 'URI': 'bitcoin:msS5WjurQ6AeKyAM3xHrsB4r1ACiLimoDx?amount=0.01', 'status': 'Pending', 'amount (BTC)': Decimal('0.01')}
```

time is UNIX timespamp of invoice, amount is amount in satoshis, exp is how much does invoice long(in seconds, value doesn't change),
address is address where users can send to,
memo is invoice description, id is invoice id, it is not used anywhere,
URI is full bitcoin url for wallets to open it,
status is status of invoice, amount (BTC) is of course amount in btc.
Only status changes there, and if invoice is paid, there is additional field confirmations showing confirmations of transaction.
Status can be one of the following:
 - Unknown
 - Pending
 - Expired
 - Paid

It is provided by electrum and statuses may change, as for now those statuses can be got from commands.py of electrum source, in definition of pr_str dictionary. For now it is [here](https://github.com/spesmilo/electrum/blob/master/electrum/commands.py#L604)

To get status of request, we use `btc.get_request(address)` method.
Note that we use address, not id.
Example(when transaction is paid):

```
btc.get_request("msS5WjurQ6AeKyAM3xHrsB4r1ACiLimoDx")
{'time': 1564678098, 'amount': 1000000, 'exp': 1200, 'address': 'msS5WjurQ6AeKyAM3xHrsB4r1ACiLimoDx', 'memo': 'My invoice description', 'id': 'd46f26f3a8', 'URI': 'bitcoin:msS5WjurQ6AeKyAM3xHrsB4r1ACiLimoDx?amount=0.01', 'status': 'Paid', 'confirmations': 0, 'amount (BTC)': Decimal('0.01')}
```

If you want to keep track of invoices, you can use event system. 

You can keep track of all changes to addresses on your account, or payment request status changes.
For that, on decorator, mark your function which you want to be capable of handling the updates with `on` decorator.

```
@btc.on("event")
def payment_handler(event, arg):
    # process it here
```

or handler for multiple events:

```
@btc.on(["event1", "event2"])
def payment_handler(event, arg):
    # process it here
```

Possible events can be found at [SDK docs](https://sdk.bitcartcc.com/en/latest/events.html).

To start listening for those updates, you need to start polling, for that, use:

`btc.poll_updates()`

Or use webhooks (starts a http server at port 6000 by default):

`btc.start_webhook()`

But note that it is run forever and it blocks your code.

To pay to some address, use
`btc.pay_to(address, amount)`

To get transaction, use `btc.get_tx(tx_hash)`

To accept updates for multiple coins, even in different currencies, you can use APIManager.

You can read about APIManager in [SDK docs](https://sdk.bitcartcc.com/en/latest/apimanager.html).

For more information, read [BitcartCC SDK docs](https://sdk.bitcartcc.com) and [Main BitcartCC docs](https://docs.bitcartcc.com)

### Telegram bot 

```
@app.on_message(filters.command("command_name"))
def some_func_name(client, message):
    # code here
```

Those samples are functions corresponding to telegram commands, like /command_name in this case.

If you see filters.regex(r'pattern') it means that it is executed when it matches regex expression, and inside function
message.matches is available to get matches as by re.search
filters.private means that command works only in private chat

withdraw function is responsible for handling messages like this:
**181AUpDVRQ3JVcb9wYLzKz2C8Rdb5mDeH7 500**

tip function is handling tips in messages like **tip!100**

deposit_query function is responsible for handling clicks on inline buttons( in "select amount you want to deposit:" message)

message.reply("text", quote=False) is a shortcut to full client.send_message(id, "text") form

We save qr codes to files directory, because right now pyrogram doesn't support uploading via bytes, only via file path or HTTP url.

For more information read [Pyrogram](https://docs.pyrogram.org) docs


### Mongo DB

In this example mongo db is used to store all data.
Mongo DB is NoSQL database, it is accessed using pymongo library
After initializing mongo client, and getting our database, we can get a collection(something similar to dayabase table in SQL databases) like so:
collection = mongo.collection_name
where mongo is MongoClient object.
To execute some action, we simply call collection.method

get_user_data returns user data by user_id and it user doesn't exist, inserts him into collection

`user = mongo.users.find_one({"user_id": user_id})` 

finds user by id, if user wasn't found, it returns None
We can use insert_one to insert into collection
find method can return list of all users in collection
update_one method updates all entries matching by first argument(filter), and sets values corresponding to
second argument(update)
$inc is special mongodb syntax, it increases value by provided value,
$set sets a new value

For more information, read [Mongo DB](https://docs.mongodb.com) and [PyMongo](https://api.mongodb.com/python/current) docs.


### QrCode

To generate qrcodes, I used qrcode library, it internally uses Pillow to save it into png format.
The api is simple:
`qrcode.make("text")` returns qrcode object, 
and `save()` method of qrcode object saves object to path specified

For more information, read [Qrcode python library](https://github.com/lincolnloop/python-qrcode/blob/master/README.rst) docs.

### f-strings

In this example I used modern python 3.6+ formatting syntax.
Basically, f-strings is a faster and better replacement for str.format() method.
You can replace old-style sentence like that:

`print("X is "+x+", Y is "+y)`

to

`print(f"X is {x}, Y is {y}")`

And no need to convert to str(), it is done automatically.
How is it done? f letter is added at the start of string(**NOT** inside the quotes)
You can also call a method, add variables and put any expression(one-line, no if's etc.) inside {}
But it is not recommended to put long expressions inside, better store it into a variable first.

For more information, read [PEP about f-strings](https://www.python.org/dev/peps/pep-0498)
