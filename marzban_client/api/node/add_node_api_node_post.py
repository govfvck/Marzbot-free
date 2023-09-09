from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.node_create import NodeCreate
from ...models.node_response import NodeResponse
from ...types import Response


def _get_kwargs(
    *,
    json_body: NodeCreate,
) -> Dict[str, Any]:
    pass

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/api/node",
        "json": json_json_body,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError, NodeResponse]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = NodeResponse.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if response.status_code == HTTPStatus.FORBIDDEN:
        response_403 = cast(Any, None)
        return response_403
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HTTPValidationError, NodeResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: NodeCreate,
) -> Response[Union[Any, HTTPValidationError, NodeResponse]]:
    r"""Add Node

    Args:
        json_body (NodeCreate):  Example: {'name': 'DE node', 'address': '192.168.1.1', 'port':
            62050, 'api_port': 62051, 'add_as_new_host': True, 'certificate': '-----BEGIN CERTIFICATE-
            ----\nMIIEnDCCAoQCAQAwDQYJKoZIhvcNAQENBQAwEzERMA8GA1UEAwwIR296YXJnYWgw\nIBcNMjMwMjE5MjMwOT
            MyWhgPMjEyMzAxMjYyMzA5MzJaMBMxETAPBgNVBAMMCEdv\nemFyZ2FoMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMI
            ICCgKCAgEA0BvDh0eU78EJ\n+xzBWUjjMrWf/0rWV5fDl7b4RU8AjeviG1RmEc64ueZ3s6q1LI6DJX1+qGuqDEvp\n
            mRc09HihO07DyQgQqF38/E4CXshZ2L3UOzsa80lf74dhEqAR/EJQXXMwGSb3T9J9\nseCqCyiEn/JLEGsilDz64cTv
            8MXMAcjjpdefkFyQP+4hAKQgHbtfJ9KPSu4/lkZR\n/orsjoWGJv4LS0MsXV1t7LB/bNC7qOzlmzrfTMH4EmtmKH8H
            whMkL1nUG+vXEfwm\nQg3Ly+yrwKNw9+L7DxbKnoy2Zqp9dN+rzKDgcpHsoIYf0feInUHHlRUu303kAFQN\nGlnzZg
            D8ulHI1sQLNS3teYpj817G3EXKOhu56MvBehBR9GfvfS1D5D/QvwRfcaZI\nCULBPoGqovhrknbUXt9TEfzc9YnfSz
            lcJYcH54/aUBVJNs74EK38OQ+JciLnw4qe\ngbXEshaeLgGM3bhXwUhctcmZf5ASWDsAVtEeCXGNK+ua6wlFXKVd0j
            Ot2ZZYG42X\nwrpHCErAWY7AoxHmXlfPcPM0Uu7FuEBP27f8U3N+glG1lWrogNn54j1ZrzQVUVVv\ngog78DrjjzrR
            0puQ9x9q6FvEUTAaaA06lvi2/6BuwO0jKrHQCP7fFUmRXg5B5lrJ\n9czSDHT9WH9Sc1qdxQTevhc9C/h6MuMCAwEA
            ATANBgkqhkiG9w0BAQ0FAAOCAgEA\nI7aXhLejp53NyuwzmdfeycY373TI4sD3WfPdEB6+FSCX38YghyQl8tkeaHPg
            PKY5\n+vA+eVxE7E961UNPtJtJg/dzBvoWUroTnpvKjVdDImFaZa/PvUMgSEe8tC3FtB6i\nAp7f0yYOGsFf6oaOxM
            fs/F0sGflsaVWuiATTsV8Er+uzge77Q8AXzy6spuXg3ALF\n56tqzZY5x/04g1KUQB4JN+7JzipnfSIUof0eAKf9gQ
            bumUU+Q2b32HMC2MOlUjv+\nIl8rJ9cs0zwC1BOmqoS3Ez22dgtT7FucvIJ1MGP8oUAudMmrXDxx/d7CmnD5q1v4\n
            XFSa6Zv8LPLCz5iMbo0FjNlKyZo3699PtyBFXt3zyfTPmiy19RVGTziHqJ9NR9kW\nkBwvFzIy+qPc/dJAk435hVaV
            3pRBC7Pl2Y7k/pJxxlC07PkACXuhwtUGhQrHYWkK\niLlV21kNnWuvjS1orTwvuW3aagb6tvEEEmlMhw5a2B8sl71s
            Q6sxWidgRaOSGW7l\ng1gctfdLMARuV6LkLiGy5k2FGAW/tfepEyySA/N9WhcHg+rZ4/x1thP0eYJPQ2YJ\nAjimHy
            Bb+3tFs7KaOPu9G5xgbQWUWccukMDXqybqiUDSfU/T5/+XM8CKq/Fu0DBu\n3lg0NYigkZFs99lZJ1H4BkMWgL65ay
            bO4XwfZJTGLe0=\n-----END CERTIFICATE-----'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError, NodeResponse]]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    json_body: NodeCreate,
) -> Optional[Union[Any, HTTPValidationError, NodeResponse]]:
    r"""Add Node

    Args:
        json_body (NodeCreate):  Example: {'name': 'DE node', 'address': '192.168.1.1', 'port':
            62050, 'api_port': 62051, 'add_as_new_host': True, 'certificate': '-----BEGIN CERTIFICATE-
            ----\nMIIEnDCCAoQCAQAwDQYJKoZIhvcNAQENBQAwEzERMA8GA1UEAwwIR296YXJnYWgw\nIBcNMjMwMjE5MjMwOT
            MyWhgPMjEyMzAxMjYyMzA5MzJaMBMxETAPBgNVBAMMCEdv\nemFyZ2FoMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMI
            ICCgKCAgEA0BvDh0eU78EJ\n+xzBWUjjMrWf/0rWV5fDl7b4RU8AjeviG1RmEc64ueZ3s6q1LI6DJX1+qGuqDEvp\n
            mRc09HihO07DyQgQqF38/E4CXshZ2L3UOzsa80lf74dhEqAR/EJQXXMwGSb3T9J9\nseCqCyiEn/JLEGsilDz64cTv
            8MXMAcjjpdefkFyQP+4hAKQgHbtfJ9KPSu4/lkZR\n/orsjoWGJv4LS0MsXV1t7LB/bNC7qOzlmzrfTMH4EmtmKH8H
            whMkL1nUG+vXEfwm\nQg3Ly+yrwKNw9+L7DxbKnoy2Zqp9dN+rzKDgcpHsoIYf0feInUHHlRUu303kAFQN\nGlnzZg
            D8ulHI1sQLNS3teYpj817G3EXKOhu56MvBehBR9GfvfS1D5D/QvwRfcaZI\nCULBPoGqovhrknbUXt9TEfzc9YnfSz
            lcJYcH54/aUBVJNs74EK38OQ+JciLnw4qe\ngbXEshaeLgGM3bhXwUhctcmZf5ASWDsAVtEeCXGNK+ua6wlFXKVd0j
            Ot2ZZYG42X\nwrpHCErAWY7AoxHmXlfPcPM0Uu7FuEBP27f8U3N+glG1lWrogNn54j1ZrzQVUVVv\ngog78DrjjzrR
            0puQ9x9q6FvEUTAaaA06lvi2/6BuwO0jKrHQCP7fFUmRXg5B5lrJ\n9czSDHT9WH9Sc1qdxQTevhc9C/h6MuMCAwEA
            ATANBgkqhkiG9w0BAQ0FAAOCAgEA\nI7aXhLejp53NyuwzmdfeycY373TI4sD3WfPdEB6+FSCX38YghyQl8tkeaHPg
            PKY5\n+vA+eVxE7E961UNPtJtJg/dzBvoWUroTnpvKjVdDImFaZa/PvUMgSEe8tC3FtB6i\nAp7f0yYOGsFf6oaOxM
            fs/F0sGflsaVWuiATTsV8Er+uzge77Q8AXzy6spuXg3ALF\n56tqzZY5x/04g1KUQB4JN+7JzipnfSIUof0eAKf9gQ
            bumUU+Q2b32HMC2MOlUjv+\nIl8rJ9cs0zwC1BOmqoS3Ez22dgtT7FucvIJ1MGP8oUAudMmrXDxx/d7CmnD5q1v4\n
            XFSa6Zv8LPLCz5iMbo0FjNlKyZo3699PtyBFXt3zyfTPmiy19RVGTziHqJ9NR9kW\nkBwvFzIy+qPc/dJAk435hVaV
            3pRBC7Pl2Y7k/pJxxlC07PkACXuhwtUGhQrHYWkK\niLlV21kNnWuvjS1orTwvuW3aagb6tvEEEmlMhw5a2B8sl71s
            Q6sxWidgRaOSGW7l\ng1gctfdLMARuV6LkLiGy5k2FGAW/tfepEyySA/N9WhcHg+rZ4/x1thP0eYJPQ2YJ\nAjimHy
            Bb+3tFs7KaOPu9G5xgbQWUWccukMDXqybqiUDSfU/T5/+XM8CKq/Fu0DBu\n3lg0NYigkZFs99lZJ1H4BkMWgL65ay
            bO4XwfZJTGLe0=\n-----END CERTIFICATE-----'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError, NodeResponse]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: NodeCreate,
) -> Response[Union[Any, HTTPValidationError, NodeResponse]]:
    r"""Add Node

    Args:
        json_body (NodeCreate):  Example: {'name': 'DE node', 'address': '192.168.1.1', 'port':
            62050, 'api_port': 62051, 'add_as_new_host': True, 'certificate': '-----BEGIN CERTIFICATE-
            ----\nMIIEnDCCAoQCAQAwDQYJKoZIhvcNAQENBQAwEzERMA8GA1UEAwwIR296YXJnYWgw\nIBcNMjMwMjE5MjMwOT
            MyWhgPMjEyMzAxMjYyMzA5MzJaMBMxETAPBgNVBAMMCEdv\nemFyZ2FoMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMI
            ICCgKCAgEA0BvDh0eU78EJ\n+xzBWUjjMrWf/0rWV5fDl7b4RU8AjeviG1RmEc64ueZ3s6q1LI6DJX1+qGuqDEvp\n
            mRc09HihO07DyQgQqF38/E4CXshZ2L3UOzsa80lf74dhEqAR/EJQXXMwGSb3T9J9\nseCqCyiEn/JLEGsilDz64cTv
            8MXMAcjjpdefkFyQP+4hAKQgHbtfJ9KPSu4/lkZR\n/orsjoWGJv4LS0MsXV1t7LB/bNC7qOzlmzrfTMH4EmtmKH8H
            whMkL1nUG+vXEfwm\nQg3Ly+yrwKNw9+L7DxbKnoy2Zqp9dN+rzKDgcpHsoIYf0feInUHHlRUu303kAFQN\nGlnzZg
            D8ulHI1sQLNS3teYpj817G3EXKOhu56MvBehBR9GfvfS1D5D/QvwRfcaZI\nCULBPoGqovhrknbUXt9TEfzc9YnfSz
            lcJYcH54/aUBVJNs74EK38OQ+JciLnw4qe\ngbXEshaeLgGM3bhXwUhctcmZf5ASWDsAVtEeCXGNK+ua6wlFXKVd0j
            Ot2ZZYG42X\nwrpHCErAWY7AoxHmXlfPcPM0Uu7FuEBP27f8U3N+glG1lWrogNn54j1ZrzQVUVVv\ngog78DrjjzrR
            0puQ9x9q6FvEUTAaaA06lvi2/6BuwO0jKrHQCP7fFUmRXg5B5lrJ\n9czSDHT9WH9Sc1qdxQTevhc9C/h6MuMCAwEA
            ATANBgkqhkiG9w0BAQ0FAAOCAgEA\nI7aXhLejp53NyuwzmdfeycY373TI4sD3WfPdEB6+FSCX38YghyQl8tkeaHPg
            PKY5\n+vA+eVxE7E961UNPtJtJg/dzBvoWUroTnpvKjVdDImFaZa/PvUMgSEe8tC3FtB6i\nAp7f0yYOGsFf6oaOxM
            fs/F0sGflsaVWuiATTsV8Er+uzge77Q8AXzy6spuXg3ALF\n56tqzZY5x/04g1KUQB4JN+7JzipnfSIUof0eAKf9gQ
            bumUU+Q2b32HMC2MOlUjv+\nIl8rJ9cs0zwC1BOmqoS3Ez22dgtT7FucvIJ1MGP8oUAudMmrXDxx/d7CmnD5q1v4\n
            XFSa6Zv8LPLCz5iMbo0FjNlKyZo3699PtyBFXt3zyfTPmiy19RVGTziHqJ9NR9kW\nkBwvFzIy+qPc/dJAk435hVaV
            3pRBC7Pl2Y7k/pJxxlC07PkACXuhwtUGhQrHYWkK\niLlV21kNnWuvjS1orTwvuW3aagb6tvEEEmlMhw5a2B8sl71s
            Q6sxWidgRaOSGW7l\ng1gctfdLMARuV6LkLiGy5k2FGAW/tfepEyySA/N9WhcHg+rZ4/x1thP0eYJPQ2YJ\nAjimHy
            Bb+3tFs7KaOPu9G5xgbQWUWccukMDXqybqiUDSfU/T5/+XM8CKq/Fu0DBu\n3lg0NYigkZFs99lZJ1H4BkMWgL65ay
            bO4XwfZJTGLe0=\n-----END CERTIFICATE-----'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError, NodeResponse]]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: NodeCreate,
) -> Optional[Union[Any, HTTPValidationError, NodeResponse]]:
    r"""Add Node

    Args:
        json_body (NodeCreate):  Example: {'name': 'DE node', 'address': '192.168.1.1', 'port':
            62050, 'api_port': 62051, 'add_as_new_host': True, 'certificate': '-----BEGIN CERTIFICATE-
            ----\nMIIEnDCCAoQCAQAwDQYJKoZIhvcNAQENBQAwEzERMA8GA1UEAwwIR296YXJnYWgw\nIBcNMjMwMjE5MjMwOT
            MyWhgPMjEyMzAxMjYyMzA5MzJaMBMxETAPBgNVBAMMCEdv\nemFyZ2FoMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMI
            ICCgKCAgEA0BvDh0eU78EJ\n+xzBWUjjMrWf/0rWV5fDl7b4RU8AjeviG1RmEc64ueZ3s6q1LI6DJX1+qGuqDEvp\n
            mRc09HihO07DyQgQqF38/E4CXshZ2L3UOzsa80lf74dhEqAR/EJQXXMwGSb3T9J9\nseCqCyiEn/JLEGsilDz64cTv
            8MXMAcjjpdefkFyQP+4hAKQgHbtfJ9KPSu4/lkZR\n/orsjoWGJv4LS0MsXV1t7LB/bNC7qOzlmzrfTMH4EmtmKH8H
            whMkL1nUG+vXEfwm\nQg3Ly+yrwKNw9+L7DxbKnoy2Zqp9dN+rzKDgcpHsoIYf0feInUHHlRUu303kAFQN\nGlnzZg
            D8ulHI1sQLNS3teYpj817G3EXKOhu56MvBehBR9GfvfS1D5D/QvwRfcaZI\nCULBPoGqovhrknbUXt9TEfzc9YnfSz
            lcJYcH54/aUBVJNs74EK38OQ+JciLnw4qe\ngbXEshaeLgGM3bhXwUhctcmZf5ASWDsAVtEeCXGNK+ua6wlFXKVd0j
            Ot2ZZYG42X\nwrpHCErAWY7AoxHmXlfPcPM0Uu7FuEBP27f8U3N+glG1lWrogNn54j1ZrzQVUVVv\ngog78DrjjzrR
            0puQ9x9q6FvEUTAaaA06lvi2/6BuwO0jKrHQCP7fFUmRXg5B5lrJ\n9czSDHT9WH9Sc1qdxQTevhc9C/h6MuMCAwEA
            ATANBgkqhkiG9w0BAQ0FAAOCAgEA\nI7aXhLejp53NyuwzmdfeycY373TI4sD3WfPdEB6+FSCX38YghyQl8tkeaHPg
            PKY5\n+vA+eVxE7E961UNPtJtJg/dzBvoWUroTnpvKjVdDImFaZa/PvUMgSEe8tC3FtB6i\nAp7f0yYOGsFf6oaOxM
            fs/F0sGflsaVWuiATTsV8Er+uzge77Q8AXzy6spuXg3ALF\n56tqzZY5x/04g1KUQB4JN+7JzipnfSIUof0eAKf9gQ
            bumUU+Q2b32HMC2MOlUjv+\nIl8rJ9cs0zwC1BOmqoS3Ez22dgtT7FucvIJ1MGP8oUAudMmrXDxx/d7CmnD5q1v4\n
            XFSa6Zv8LPLCz5iMbo0FjNlKyZo3699PtyBFXt3zyfTPmiy19RVGTziHqJ9NR9kW\nkBwvFzIy+qPc/dJAk435hVaV
            3pRBC7Pl2Y7k/pJxxlC07PkACXuhwtUGhQrHYWkK\niLlV21kNnWuvjS1orTwvuW3aagb6tvEEEmlMhw5a2B8sl71s
            Q6sxWidgRaOSGW7l\ng1gctfdLMARuV6LkLiGy5k2FGAW/tfepEyySA/N9WhcHg+rZ4/x1thP0eYJPQ2YJ\nAjimHy
            Bb+3tFs7KaOPu9G5xgbQWUWccukMDXqybqiUDSfU/T5/+XM8CKq/Fu0DBu\n3lg0NYigkZFs99lZJ1H4BkMWgL65ay
            bO4XwfZJTGLe0=\n-----END CERTIFICATE-----'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError, NodeResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
