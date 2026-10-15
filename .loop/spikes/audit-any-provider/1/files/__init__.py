"""Spike plugin: offer read_file/search_files under a read-only toolset."""
import copy

from tools import file_tools as ft


def _schema(base, name):
    s = copy.deepcopy(base)
    s["name"] = name
    return s


def register(ctx):
    ctx.register_tool(name="kmctl_read_file", toolset="kmctl_read",
                      schema=_schema(ft.READ_FILE_SCHEMA, "kmctl_read_file"),
                      handler=lambda args, **kw: ft._handle_read_file(args, **kw),
                      check_fn=ft._check_file_reqs)
    ctx.register_tool(name="kmctl_search_files", toolset="kmctl_read",
                      schema=_schema(ft.SEARCH_FILES_SCHEMA, "kmctl_search_files"),
                      handler=lambda args, **kw: ft._handle_search_files(args, **kw),
                      check_fn=ft._check_file_reqs)
