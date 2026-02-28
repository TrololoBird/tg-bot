"""Top level package for the unified crypto signal bot.

This package brings together multiple disparate scanning bots into a single
system organised around clearly defined layers. The public API of the
package intentionally exposes only the components that make sense for
embedding into a larger application. Most of the heavy lifting happens
inside the ``core`` and ``scanners`` subpackages.

The code in this package does not depend on any external network or
API services being available at runtime. Where a live connection would
normally be required (for example, to retrieve market data or send
Telegram messages) the implementation falls back to simple stubs. This
approach allows developers to focus on the high‑level design and extend
or replace individual pieces as needed without being blocked by missing
dependencies.

To start the system from the command line, execute ``python -m
combined_bot.main``. See ``README.md`` for usage instructions and
architecture overview.
"""

from . import config  # noqa: F401  # reexport for convenience
from .models import MarketSymbol, SignalEvent, UserSettings  # noqa: F401