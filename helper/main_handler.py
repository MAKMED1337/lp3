import asyncio
import traceback
from collections.abc import Awaitable, Callable
from signal import SIGINT, SIGTERM

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def _main(
        main: Callable[[], Awaitable[None]],
        exception_handler: Callable[[Exception], Awaitable[None]] | None,
        clean_up: Callable[[], Awaitable[None]],
        ) -> None:
    try:
        await main()
    except Exception as e:  # noqa: BLE001
        if exception_handler:
            await exception_handler(e)
        else:
            raise
    finally:
        await clean_up()


def main_handler(
        main: Callable[[], Awaitable[None]],
        exception_handler: Callable[[Exception], Awaitable[None]] | None,
        clean_up: Callable[[], Awaitable[None]],
        ) -> None:
    main_task = loop.create_task(_main(main, exception_handler, clean_up))
    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, main_task.cancel)

    try:
        loop.run_until_complete(main_task)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    finally:
        loop.close()
