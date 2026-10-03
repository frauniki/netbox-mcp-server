"""Tests for write tools (create/update/delete, single and bulk)."""

import asyncio
from unittest.mock import patch

import pytest

from netbox_mcp_server.server import (
    mcp,
    netbox_bulk_create_objects,
    netbox_bulk_delete_objects,
    netbox_bulk_update_objects,
    netbox_create_object,
    netbox_delete_object,
    netbox_update_object,
)


@patch("netbox_mcp_server.server.netbox")
def test_create_object(mock_netbox):
    mock_netbox.create.return_value = {"id": 1, "name": "nyc"}

    result = netbox_create_object("dcim.site", {"name": "nyc", "slug": "nyc"})

    mock_netbox.create.assert_called_once_with("dcim/sites", {"name": "nyc", "slug": "nyc"})
    assert result == {"id": 1, "name": "nyc"}


@patch("netbox_mcp_server.server.netbox")
def test_update_object(mock_netbox):
    netbox_update_object("dcim.device", 5, {"status": "offline"})

    mock_netbox.update.assert_called_once_with("dcim/devices", 5, {"status": "offline"})


@patch("netbox_mcp_server.server.netbox")
def test_delete_object(mock_netbox):
    mock_netbox.delete.return_value = True

    assert netbox_delete_object("ipam.ipaddress", 7) == {"deleted": True}
    mock_netbox.delete.assert_called_once_with("ipam/ip-addresses", 7)


@patch("netbox_mcp_server.server.netbox")
def test_bulk_create_objects(mock_netbox):
    data = [{"vid": 100, "name": "a"}, {"vid": 200, "name": "b"}]

    netbox_bulk_create_objects("ipam.vlan", data)

    mock_netbox.bulk_create.assert_called_once_with("ipam/vlans", data)


@patch("netbox_mcp_server.server.netbox")
def test_bulk_update_objects(mock_netbox):
    data = [{"id": 10, "enabled": False}, {"id": 11, "enabled": False}]

    netbox_bulk_update_objects("dcim.interface", data)

    mock_netbox.bulk_update.assert_called_once_with("dcim/interfaces", data)


@patch("netbox_mcp_server.server.netbox")
def test_bulk_update_requires_id(mock_netbox):
    with pytest.raises(ValueError, match=r"missing at index \[1\]"):
        netbox_bulk_update_objects("dcim.interface", [{"id": 10}, {"enabled": False}])

    mock_netbox.bulk_update.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_bulk_delete_objects(mock_netbox):
    mock_netbox.bulk_delete.return_value = True

    assert netbox_bulk_delete_objects("ipam.ipaddress", [1, 2]) == {"deleted": True}
    mock_netbox.bulk_delete.assert_called_once_with("ipam/ip-addresses", [1, 2])


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        (netbox_create_object, ({},)),
        (netbox_update_object, (1, {})),
        (netbox_delete_object, (1,)),
        (netbox_bulk_create_objects, ([],)),
        (netbox_bulk_update_objects, ([],)),
        (netbox_bulk_delete_objects, ([],)),
    ],
)
@patch("netbox_mcp_server.server.netbox")
def test_write_tools_reject_invalid_object_type(mock_netbox, tool, args):
    with pytest.raises(ValueError, match="Invalid object_type"):
        tool("dcim.nonexistent", *args)

    assert mock_netbox.method_calls == []


@pytest.mark.parametrize(
    ("name", "destructive"),
    [
        ("netbox_create_object", False),
        ("netbox_update_object", True),
        ("netbox_delete_object", True),
        ("netbox_bulk_create_objects", False),
        ("netbox_bulk_update_objects", True),
        ("netbox_bulk_delete_objects", True),
    ],
)
def test_write_tools_annotations(name, destructive):
    tool = asyncio.run(mcp.get_tool(name))

    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is destructive
