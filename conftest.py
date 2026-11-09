from dataclasses import dataclass
from typing import Any

import httpx2
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from carton.models import *


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        # "sqlite:///test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )
    SQLModel.metadata.create_all(engine, )

    with Session(engine) as session:
        yield session


@dataclass
class _MockedResponse:
    url: str | None
    method: str | None
    response_kwargs: dict[str, Any]
    is_reusable: bool
    requested: int = 0

    def matches(self, request: httpx2.Request) -> bool:
        if self.method is not None and request.method != self.method.upper():
            return False
        if self.url is None:
            return True
        # Query parameters are compared regardless of their order
        expected = httpx2.URL(self.url)
        return (expected.copy_with(query=None) == request.url.copy_with(query=None)
                and sorted(expected.params.multi_items()) == sorted(request.url.params.multi_items()))


class HTTPXMock:
    """Answer httpx2 requests with registered responses, like pytest-httpx does for httpx.

    Each response is sent once unless it is reusable. Requests that match no
    response raise httpx2.TimeoutException and, as responses never requested,
    fail the test on teardown.
    """

    def __init__(self) -> None:
        self._responses: list[_MockedResponse] = []
        self._requests: list[httpx2.Request] = []
        self._unexpected_requests: list[httpx2.Request] = []

    def add_response(self, url: str | None = None, method: str | None = None, status_code: int = 200,
                     text: str | None = None, json: Any = None, headers: dict | None = None,
                     is_reusable: bool = False) -> None:
        response_kwargs: dict[str, Any] = {'status_code': status_code, 'headers': headers}
        if text is not None:
            response_kwargs['text'] = text
        if json is not None:
            response_kwargs['json'] = json
        self._responses.append(_MockedResponse(url, method, response_kwargs, is_reusable))

    def get_requests(self) -> list[httpx2.Request]:
        return list(self._requests)

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        self._requests.append(request)

        matching = [response for response in self._responses if response.matches(request)]
        response = (next((r for r in matching if not r.requested), None)
                    or next((r for r in matching if r.is_reusable), None))
        if response is None:
            self._unexpected_requests.append(request)
            raise httpx2.TimeoutException(f"No response can be found for {request.method} request on {request.url}",
                                          request=request)

        response.requested += 1
        return httpx2.Response(request=request, **response.response_kwargs)

    def _check(self) -> None:
        not_requested = [f"{r.method or 'ANY'} {r.url or 'ANY'}" for r in self._responses if not r.requested]
        assert not not_requested, f"Responses never requested: {not_requested}"
        unexpected = [f"{r.method} {r.url}" for r in self._unexpected_requests]
        assert not unexpected, f"Requests without response: {unexpected}"


@pytest.fixture
def httpx_mock(monkeypatch) -> Any:
    mock = HTTPXMock()
    transport = httpx2.MockTransport(mock._handle)

    # Every client created during the test sends its requests to the mock
    for client_class in (httpx2.Client, httpx2.AsyncClient):
        original_init = client_class.__init__

        def init(self, *args, _original_init=original_init, **kwargs):
            kwargs['transport'] = transport
            _original_init(self, *args, **kwargs)

        monkeypatch.setattr(client_class, '__init__', init)

    yield mock
    mock._check()
