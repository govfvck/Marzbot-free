from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.proxy_host_alpn import ProxyHostALPN
from ..models.proxy_host_fingerprint import ProxyHostFingerprint
from ..models.proxy_host_security import ProxyHostSecurity
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProxyHost")


@_attrs_define
class ProxyHost:
    """
    Attributes:
        remark (str):
        address (str):
        port (Union[Unset, None, int]):
        sni (Union[Unset, None, str]):
        host (Union[Unset, None, str]):
        security (Union[Unset, ProxyHostSecurity]): An enumeration. Default: ProxyHostSecurity.INBOUND_DEFAULT.
        alpn (Union[Unset, ProxyHostALPN]): An enumeration. Default: ProxyHostALPN.VALUE_0.
        fingerprint (Union[Unset, ProxyHostFingerprint]): An enumeration. Default: ProxyHostFingerprint.VALUE_0.
    """

    remark: str
    address: str
    port: Union[Unset, None, int] = UNSET
    sni: Union[Unset, None, str] = UNSET
    host: Union[Unset, None, str] = UNSET
    security: Union[Unset, ProxyHostSecurity] = ProxyHostSecurity.INBOUND_DEFAULT
    alpn: Union[Unset, ProxyHostALPN] = ProxyHostALPN.VALUE_0
    fingerprint: Union[Unset, ProxyHostFingerprint] = ProxyHostFingerprint.VALUE_0
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        remark = self.remark
        address = self.address
        port = self.port
        sni = self.sni
        host = self.host
        security: Union[Unset, str] = UNSET
        if not isinstance(self.security, Unset):
            security = self.security.value

        alpn: Union[Unset, str] = UNSET
        if not isinstance(self.alpn, Unset):
            alpn = self.alpn.value

        fingerprint: Union[Unset, str] = UNSET
        if not isinstance(self.fingerprint, Unset):
            fingerprint = self.fingerprint.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "remark": remark,
                "address": address,
            }
        )
        if port is not UNSET:
            field_dict["port"] = port
        if sni is not UNSET:
            field_dict["sni"] = sni
        if host is not UNSET:
            field_dict["host"] = host
        if security is not UNSET:
            field_dict["security"] = security
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if fingerprint is not UNSET:
            field_dict["fingerprint"] = fingerprint

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        remark = d.pop("remark")

        address = d.pop("address")

        port = d.pop("port", UNSET)

        sni = d.pop("sni", UNSET)

        host = d.pop("host", UNSET)

        _security = d.pop("security", UNSET)
        security: Union[Unset, ProxyHostSecurity]
        if isinstance(_security, Unset):
            security = UNSET
        else:
            security = ProxyHostSecurity(_security)

        _alpn = d.pop("alpn", UNSET)
        alpn: Union[Unset, ProxyHostALPN]
        if isinstance(_alpn, Unset):
            alpn = UNSET
        else:
            alpn = ProxyHostALPN(_alpn)

        _fingerprint = d.pop("fingerprint", UNSET)
        fingerprint: Union[Unset, ProxyHostFingerprint]
        if isinstance(_fingerprint, Unset):
            fingerprint = UNSET
        else:
            fingerprint = ProxyHostFingerprint(_fingerprint)

        proxy_host = cls(
            remark=remark,
            address=address,
            port=port,
            sni=sni,
            host=host,
            security=security,
            alpn=alpn,
            fingerprint=fingerprint,
        )

        proxy_host.additional_properties = d
        return proxy_host

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
