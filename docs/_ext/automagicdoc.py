import io
import os
import shutil
from fnmatch import fnmatch
from importlib import import_module
from pathlib import Path

import docutils.io

base_path = os.getcwd()
virtual_files = {}


real_os_walk = os.walk


def new_os_walk(*args, **kwargs):
    for path, dirs, files in real_os_walk(*args, **kwargs):
        if path == base_path:
            files += [
                virtual_file_name.split('/')[-1]
                for virtual_file_name in virtual_files.keys()
            ]
        yield path, dirs, files


os.walk = new_os_walk


real_os_access = os.access


def new_os_access(*args, **kwargs):
    for virtual_file_name in virtual_files.keys():
        if args[0] == os.path.join(base_path, virtual_file_name):
            return True

    return real_os_access(*args, **kwargs)


os.access = new_os_access


real_os_stat = os.stat


def new_os_stat(*args, **kwargs):
    for virtual_file_name in virtual_files.keys():
        if args[0] == os.path.join(base_path, virtual_file_name):
            return os.stat_result([0] * 10)

    return real_os_stat(*args, **kwargs)


os.stat = new_os_stat


real_open = open


def new_open(*args, **kwargs):
    for virtual_file_name in virtual_files.keys():
        if args[0] == os.path.join(base_path, virtual_file_name):
            return io.TextIOWrapper(
                io.BytesIO(virtual_files[virtual_file_name].encode('utf-8'))
            )

    return real_open(*args, **kwargs)


docutils.io.open = new_open


real_copyfile = shutil.copyfile


def new_copyfile(*args, **kwargs):
    for virtual_file_name in virtual_files.keys():
        if args[0] == os.path.join(base_path, virtual_file_name):
            with open(args[1], 'w+') as fp:
                fp.write(virtual_files[virtual_file_name])
            return True
    return real_copyfile(*args, **kwargs)


shutil.copyfile = new_copyfile


##############

from collections import namedtuple

Module = namedtuple(
    'Module', ['module_str', 'is_package', 'has_submodules', 'parent_str']
)


def get_submodules(name, ignore=None):
    if ignore is None:
        ignore = []

    if isinstance(name, str):
        module = import_module(name)
    else:
        module = name

    base_path = Path(module.__file__).parent

    def path_to_str(p):
        s = str(p).replace(str(base_path.parent), '').replace('/', '.')
        if s.startswith('.'):
            s = s[1:]
        if s.endswith('.py'):
            s = s[:-3]
        return s

    def is_ignored(what):
        s = path_to_str(what)
        for i in ignore:
            if fnmatch(s, i):
                return True
        return False

    submodules = [
        p for p in sorted(base_path.rglob('__init__.py')) if not is_ignored(p.parent)
    ]

    for submodule in submodules:
        submodule = submodule.parent
        subsubmodules = [
            subsubmodule
            for subsubmodule in submodule.glob('*.py')
            if subsubmodule.name not in ('__init__.py', '__main__.py')
            and not is_ignored(subsubmodule)
        ]

        submodule_str = path_to_str(submodule)

        yield Module(
            module_str=submodule_str,
            is_package=True,
            has_submodules=bool(len(subsubmodules)),
            parent_str='.'.join(submodule_str.split('.')[:-1]),
        )

        for subsubmodule in subsubmodules:
            yield Module(
                module_str=path_to_str(subsubmodule),
                is_package=False,
                has_submodules=False,
                parent_str=submodule_str,
            )


#########
def escape(s):
    return s.replace('_', '\\_')


def prepare_rst_content(submodule, submodules):

    result = ""

    title = f"{escape(submodule.module_str)} package"

    subpackages = "\n".join(
        [
            f"   {m.module_str}"
            for m in submodules
            if m.parent_str == submodule.module_str and m.is_package
        ]
    )

    subpackages_block = """.. Subpackages
.. -----------

.. toctree::
   :maxdepth: 4
"""

    result += f"""
{title}
{"=" * len(title)}

.. automodule:: {submodule.module_str}
   :members:
   :undoc-members:
   :show-inheritance:
   
{subpackages_block if subpackages else ""}
{subpackages}

    """

    subsubmodules = [
        m
        for m in submodules
        if m.parent_str == submodule.module_str and not m.is_package
    ]

    if len(subsubmodules):
        result += """
.. Submodules
.. ----------
    """

    for subsubmodule in subsubmodules:
        sub_title = f"{escape(subsubmodule.module_str)} module"
        result += f"""
{sub_title}
{"+" * len(sub_title)}

.. automodule:: {subsubmodule.module_str}
   :members:
   :undoc-members:
   :show-inheritance:
    """

    return result


def setup(app):
    def config_inited(app, config):
        global base_path
        base_path = app.srcdir

        for module in config.automagic_modules:
            submodules = list(get_submodules(module, ignore=config.automagic_ignore))

            for submodule in submodules:
                if not submodule.is_package:
                    continue

                result = prepare_rst_content(submodule, submodules)

                virtual_files[submodule.module_str + '.rst'] = result

    app.connect('config-inited', config_inited)
    app.add_config_value(
        name='automagic_modules', default=[], rebuild='env', types=[list]
    )
    app.add_config_value(
        name='automagic_ignore', default=[], rebuild='env', types=[list]
    )
