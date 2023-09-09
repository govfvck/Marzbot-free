from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_core_config_api_core_config_get_response_get_core_config_api_core_config_get import (
    GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet,
)
from ...types import Response


def _get_kwargs() -> Dict[str, Any]:
    pass

    return {
        "method": "get",
        "url": "/api/core/config",
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == HTTPStatus.FORBIDDEN:
        response_403 = cast(Any, None)
        return response_403
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    """Get Core Config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    """Get Core Config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    """Get Core Config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
]:
    """Get Core Config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetCoreConfigApiCoreConfigGetResponseGetCoreConfigApiCoreConfigGet]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
