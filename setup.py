from setuptools import setup, find_packages

version = '0.1'

setup(
      name='sudoku',
      version=version,
      description="Logical Sudoku Solver",
      long_description="""Logical Sudoku Solver""",
      packages=['sudoku'],
      author='Matthew Drury',
      tests_require = ['pytest'],
      zip_safe=False
)