from typing import List

from discord.ext.commands import Context

import config

def madi_only(func):
    def wrapper(*args, **kwargs):
        print(kwargs)
        if "ctx" not in kwargs:
            return
        if kwargs["ctx"].author.id != config.madi_id:
            return
        func(*args, **kwargs)
    return wrapper


def parse_args(ctx: Context) -> List[str]:
    args = ctx.message.content
    for p in config.command_prefixes:
        args = args.replace(f"{p}{ctx.invoked_with} ", "")
    args = remove_empty_items(args.replace("\n", " \n").split(" "))
    return args

def remove_empty_items(items: list) -> List[str]:
    for _ in range(items.count("")):
        items.remove("")
    return items
