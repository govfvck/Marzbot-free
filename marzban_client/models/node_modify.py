from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NodeModify")


@_attrs_define
class NodeModify:
    r"""
    Example:
        {'name': 'DE node', 'address': '192.168.1.1', 'port': 62050, 'api_port': 62051, 'certificate': '-----BEGIN CERTI
            FICATE-----
            \nMIIEnDCCAoQCAQAwDQYJKoZIhvcNAQENBQAwEzERMA8GA1UEAwwIR296YXJnYWgw\nIBcNMjMwMjE5MjMwOTMyWhgPMjEyMzAxMjYyMzA5MzJa
            MBMxETAPBgNVBAMMCEdv\nemFyZ2FoMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA0BvDh0eU78EJ\n+xzBWUjjMrWf/0rWV5fDl7b4
            RU8AjeviG1RmEc64ueZ3s6q1LI6DJX1+qGuqDEvp\nmRc09HihO07DyQgQqF38/E4CXshZ2L3UOzsa80lf74dhEqAR/EJQXXMwGSb3T9J9\nseCq
            CyiEn/JLEGsilDz64cTv8MXMAcjjpdefkFyQP+4hAKQgHbtfJ9KPSu4/lkZR\n/orsjoWGJv4LS0MsXV1t7LB/bNC7qOzlmzrfTMH4EmtmKH8Hwh
            MkL1nUG+vXEfwm\nQg3Ly+yrwKNw9+L7DxbKnoy2Zqp9dN+rzKDgcpHsoIYf0feInUHHlRUu303kAFQN\nGlnzZgD8ulHI1sQLNS3teYpj817G3E
            XKOhu56MvBehBR9GfvfS1D5D/QvwRfcaZI\nCULBPoGqovhrknbUXt9TEfzc9YnfSzlcJYcH54/aUBVJNs74EK38OQ+JciLnw4qe\ngbXEshaeLg
            GM3bhXwUhctcmZf5ASWDsAVtEeCXGNK+ua6wlFXKVd0jOt2ZZYG42X\nwrpHCErAWY7AoxHmXlfPcPM0Uu7FuEBP27f8U3N+glG1lWrogNn54j1Z
            rzQVUVVv\ngog78DrjjzrR0puQ9x9q6FvEUTAaaA06lvi2/6BuwO0jKrHQCP7fFUmRXg5B5lrJ\n9czSDHT9WH9Sc1qdxQTevhc9C/h6MuMCAwEA
            ATANBgkqhkiG9w0BAQ0FAAOCAgEA\nI7aXhLejp53NyuwzmdfeycY373TI4sD3WfPdEB6+FSCX38YghyQl8tkeaHPgPKY5\n+vA+eVxE7E961UNP
            tJtJg/dzBvoWUroTnpvKjVdDImFaZa/PvUMgSEe8tC3FtB6i\nAp7f0yYOGsFf6oaOxMfs/F0sGflsaVWuiATTsV8Er+uzge77Q8AXzy6spuXg3A
            LF\n56tqzZY5x/04g1KUQB4JN+7JzipnfSIUof0eAKf9gQbumUU+Q2b32HMC2MOlUjv+\nIl8rJ9cs0zwC1BOmqoS3Ez22dgtT7FucvIJ1MGP8oU
            AudMmrXDxx/d7CmnD5q1v4\nXFSa6Zv8LPLCz5iMbo0FjNlKyZo3699PtyBFXt3zyfTPmiy19RVGTziHqJ9NR9kW\nkBwvFzIy+qPc/dJAk435hV
            aV3pRBC7Pl2Y7k/pJxxlC07PkACXuhwtUGhQrHYWkK\niLlV21kNnWuvjS1orTwvuW3aagb6tvEEEmlMhw5a2B8sl71sQ6sxWidgRaOSGW7l\ng1
            gctfdLMARuV6LkLiGy5k2FGAW/tfepEyySA/N9WhcHg+rZ4/x1thP0eYJPQ2YJ\nAjimHyBb+3tFs7KaOPu9G5xgbQWUWccukMDXqybqiUDSfU/T
            5/+XM8CKq/Fu0DBu\n3lg0NYigkZFs99lZJ1H4BkMWgL65aybO4XwfZJTGLe0=\n-----END CERTIFICATE-----'}

    Attributes:
        name (Union[Unset, None, str]):
        address (Union[Unset, None, str]):
        port (Union[Unset, None, int]):
        api_port (Union[Unset, None, int]):
        certificate (Union[Unset, None, str]):
    """

    name: Union[Unset, None, str] = UNSET
    address: Union[Unset, None, str] = UNSET
    port: Union[Unset, None, int] = UNSET
    api_port: Union[Unset, None, int] = UNSET
    certificate: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        address = self.address
        port = self.port
        api_port = self.api_port
        certificate = self.certificate

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if address is not UNSET:
            field_dict["address"] = address
        if port is not UNSET:
            field_dict["port"] = port
        if api_port is not UNSET:
            field_dict["api_port"] = api_port
        if certificate is not UNSET:
            field_dict["certificate"] = certificate

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        address = d.pop("address", UNSET)

        port = d.pop("port", UNSET)

        api_port = d.pop("api_port", UNSET)

        certificate = d.pop("certificate", UNSET)

        node_modify = cls(
            name=name,
            address=address,
            port=port,
            api_port=api_port,
            certificate=certificate,
        )

        node_modify.additional_properties = d
        return node_modify

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
