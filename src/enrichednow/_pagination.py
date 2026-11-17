"""Cursor pagination. A list answers one page and a `next_cursor`; `None` means there is no next page.

Iterating a page walks every item of it and of all the pages after it, fetching each page as it is reached:

    for record in client.runs.records(run_id):
        ...

For one page at a time, use `.items`, `.next_cursor`, `.has_next_page()`, `.next_page()` and `.iter_pages()`.
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Generator, Generic, Iterator, List, Optional, TypeVar

__all__ = ["SyncPage", "AsyncPage", "SyncRecordsPage", "AsyncRecordsPage", "AsyncPaginator"]

T = TypeVar("T")
SP = TypeVar("SP", bound="SyncPage[Any]")
AP = TypeVar("AP", bound="AsyncPage[Any]")


class _Page(Generic[T]):
    def __init__(self, items: List[T], next_cursor: Optional[str], raw: Dict[str, Any]) -> None:
        self.items = items
        """The items of this page."""
        self.next_cursor = next_cursor
        """The cursor of the next page; `None` on the last one."""
        self.raw = raw
        """The JSON object as the API returned it."""

    def has_next_page(self) -> bool:
        return self.next_cursor is not None

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(items={len(self.items)}, next_cursor={self.next_cursor!r})"


class SyncPage(_Page[T]):
    """One page of a list. Iterating it yields its items and then those of every later page."""

    _fetch: Callable[[Optional[str]], Any]

    def next_page(self: SP) -> Optional[SP]:
        """The next page, or `None` on the last one."""
        if self.next_cursor is None:
            return None
        page: SP = self._fetch(self.next_cursor)
        return page

    def iter_pages(self: SP) -> Iterator[SP]:
        """This page and every page after it."""
        page: Optional[SP] = self
        while page is not None:
            yield page
            page = page.next_page()

    def __iter__(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.items

    def to_list(self) -> List[T]:
        """Every item of this page and of all the pages after it."""
        return list(self)


class AsyncPage(_Page[T]):
    """One page of a list. `async for` over it yields its items and then those of every later page."""

    _fetch: Callable[[Optional[str]], Awaitable[Any]]

    async def next_page(self: AP) -> Optional[AP]:
        """The next page, or `None` on the last one."""
        if self.next_cursor is None:
            return None
        page: AP = await self._fetch(self.next_cursor)
        return page

    async def iter_pages(self: AP) -> AsyncIterator[AP]:
        """This page and every page after it."""
        page: Optional[AP] = self
        while page is not None:
            yield page
            page = await page.next_page()

    async def __aiter__(self) -> AsyncIterator[T]:
        async for page in self.iter_pages():
            for item in page.items:
                yield item

    async def to_list(self) -> List[T]:
        """Every item of this page and of all the pages after it."""
        return [item async for item in self]


class SyncRecordsPage(SyncPage[Dict[str, Any]]):
    """A page of a run's records. `expired` is true when the records are gone (they are kept 7 days after the run ended)."""

    expired: bool = False


class AsyncRecordsPage(AsyncPage[Dict[str, Any]]):
    """A page of a run's records. `expired` is true when the records are gone (they are kept 7 days after the run ended)."""

    expired: bool = False


class AsyncPaginator(Generic[T, AP]):
    """What the async client's list methods return. Await it for the first page, or `async for` over it for every item:

        page = await client.runs.list()
        async for run in client.runs.list():
            ...
    """

    def __init__(self, fetch: Callable[[Optional[str]], Awaitable[AP]], cursor: Optional[str] = None) -> None:
        self._fetch = fetch
        self._cursor = cursor

    def __await__(self) -> Generator[Any, None, AP]:
        return self._fetch(self._cursor).__await__()

    async def __aiter__(self) -> AsyncIterator[T]:
        page = await self._fetch(self._cursor)
        async for item in page:
            yield item

    async def iter_pages(self) -> AsyncIterator[AP]:
        """Every page, from the first."""
        page = await self._fetch(self._cursor)
        async for each in page.iter_pages():
            yield each

    async def to_list(self) -> List[T]:
        """Every item of every page."""
        return [item async for item in self]
