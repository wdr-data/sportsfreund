import os


def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__

    if not os.environ.get('CI'):
        item._nodeid = ' - '.join((pref, suf))
    else:
        item._location = (f'{item.location[0]} | {pref} ', item.location[1], f' {suf}')
