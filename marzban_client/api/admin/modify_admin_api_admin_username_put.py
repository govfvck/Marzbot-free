from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.admin import Admin
from ...models.admin_modify import AdminModify
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    username: str,
    *,
    json_body: AdminModify,
) -> Dict[str, Any]:
    pass

    json_json_body = json_body.to_dict()

    return {
        "method": "put",
        "url": "/api/admin/{username}".format(
            username=username,
        ),
        "json": json_json_body,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Admin, Any, HTTPValidationError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = Admin.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if response.status_code == HTTPStatus.FORBIDDEN:
        response_403 = cast(Any, None)
        return response_403
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = cast(Any, None)
        return response_404
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Admin, Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: AdminModify,
) -> Response[Union[Admin, Any, HTTPValidationError]]:
    """Modify Admin

    Args:
        username (str):
        json_body (AdminModify):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Admin, Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        json_body=json_body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: AdminModify,
) -> Optional[Union[Admin, Any, HTTPValidationError]]:
    """Modify Admin

    Args:
        username (str):
        json_body (AdminModify):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Admin, Any, HTTPValidationError]
    """

    return sync_detailed(
        username=username,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: AdminModify,
) -> Response[Union[Admin, Any, HTTPValidationError]]:
    """Modify Admin

    Args:
        username (str):
        json_body (AdminModify):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Admin, Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        json_body=json_body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: AdminModify,
) -> Optional[Union[Admin, Any, HTTPValidationError]]:
    """Modify Admin

    Args:
        username (str):
        json_body (AdminModify):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Admin, Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            username=username,
            client=client,
            json_body=json_body,
        )
    ).parsed
