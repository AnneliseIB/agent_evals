# Document the text utilities module

`/app/textutils.py` has no module-level docstring. Add one so that:

- It is the module's docstring: a string literal that is the first statement
  in the file, so `ast.get_docstring` and `textutils.__doc__` return it.
- Its first line is a one-sentence summary of what the module is for.
- It includes a usage example in doctest format (`>>>` prompts followed by the
  expected output) that calls `slugify`. Every example in the module docstring
  must pass when run with Python's `doctest` module.

Change nothing else in the file. Keep every import, constant, and function
exactly as it is, and do not add docstrings to the functions.
