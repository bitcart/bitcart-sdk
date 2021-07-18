from queue import Queue

import pytest

test_queue = Queue()


def handler(event, tx):
    test_queue.put(2)


async def async_handler(event, height):
    test_queue.put(3)


@pytest.mark.asyncio
async def test_event_system(btc, caplog):
    assert btc.add_event_handler("event", lambda x: test_queue.put(1)) is None

    @btc.on("event")
    def func():
        test_queue.put(2)

    assert btc.add_event_handler(["event1", "event2"], lambda x: test_queue.put(1)) is None
    assert btc.add_event_handler(["new_transaction", "event2"], handler) is None
    assert btc.add_event_handler("new_block", async_handler) is None
    assert set(btc.event_handlers.keys()) == {"event", "event1", "event2", "new_transaction", "new_block"}
    assert btc.event_handlers["new_transaction"] == handler
    assert btc.event_handlers["new_block"] == async_handler
    assert await btc.process_updates({}) is None  # ignoring exceptions
    assert await btc.process_updates([[]]) is None  # ignoring exceptions
    await btc.process_updates([{}])
    assert "Invalid event from server: None" in caplog.text
    await btc.process_updates([{"event": "event"}])
    assert "Invalid event from server: event" in caplog.text
    await btc.process_updates(
        [{"event": "new_transaction"}, {"event": "new_transaction", "tx": "test"}]
    )  # ignoring invalid data, accepting valid
    await btc.process_updates([{"event": "new_block", "height": 1}])
    assert test_queue.qsize() == 2
    assert test_queue.get() == 2
    assert test_queue.get() == 3
