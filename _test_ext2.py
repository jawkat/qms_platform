import sys
sys.path.insert(0, '/app')
if 'app.extensions' in sys.modules:
    del sys.modules['app.extensions']

try:
    mod = __import__('app.extensions')
    ext_mod = getattr(mod, 'extensions')
    print('All attrs:', [x for x in dir(ext_mod) if not x.startswith('__')])
    print('--')
    print('Source file:', getattr(ext_mod, '__file__', 'unknown'))
    
    # Also check if flask_sqlalchemy works
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    print('Flask-SQLAlchemy works, db:', db)
except Exception as e:
    import traceback
    traceback.print_exc()
