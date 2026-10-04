"""Module menu registry: every NanoCom function per module (ADR-0008).

Each module's ``*/menu.py`` lists groups (``id``, ``page``, ``cat``, optional ``parent`` and
``nanocom``) of items that link a signal-store field (``sig``), registry actions
(``actions``) or, when unlinked, carry a hand ``status``. :mod:`d2diag.catalog` derives
each item's status and safety from those links and serves ``/catalog``; the admin Map tab
keeps its legacy shape through :func:`d2diag.catalog.legacy_menu`.
"""
from .ace.menu import ACE_MENU
from .airbag.menu import AIRBAG_MENU
from .autobox.menu import AUTOBOX_MENU
from .bcu.menu import BCU_MENU
from .slabs.menu import SLABS_MENU
from .td5.menu import TD5_MENU

# Order = display order in the dashboard's coverage-map picker.
MENUS: "dict[str, list]" = {
    "td5": TD5_MENU,
    "slabs": SLABS_MENU,
    "bcu": BCU_MENU,
    "ace": ACE_MENU,
    "autobox": AUTOBOX_MENU,
    "airbag": AIRBAG_MENU,
}


def menu_for(module: str) -> "list":
    return MENUS.get(module, [])
