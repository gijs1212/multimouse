import importlib.machinery, importlib.util, pathlib

_path = pathlib.Path(__file__).with_name('multimouse.pyw')
loader = importlib.machinery.SourceFileLoader('multimouse_core', str(_path))
spec = importlib.util.spec_from_loader('multimouse_core', loader)
_mod = importlib.util.module_from_spec(spec)
loader.exec_module(_mod)

globals().update(_mod.__dict__)

if __name__ == '__main__':
    _mod.main()
