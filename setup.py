from setuptools import setup

setup(
    name='rel',
    version='0.1',
    py_modules=['rel'],
    install_requires=[
        'Click',
	'PlyPlus',
	'ply',
	'storm'
    ],
    entry_points='''
        [console_scripts]
        rel=rel:nb_ui
    ''',
)
