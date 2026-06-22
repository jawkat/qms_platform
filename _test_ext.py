import sys
sys.path.insert(0, '/app')

# Remove any cached module
if 'app.extensions' in sys.modules:
    del sys.modules['app.extensions']

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('app.extensions', '/app/app/extensions.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in ['db', 'migrate', 'login_manager', 'csrf', 'mail', 'api', 'ma_plugin']:
        val = getattr(mod, attr, 'NOT FOUND')
        print(f'{attr}: {val}')
except Exception as e:
    import traceback
    traceback.print_exc()
