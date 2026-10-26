Add support for subtraction through a feature-branch workflow:

1. Create a branch named `feature/subtract` from `main`.
2. On that branch, add the following function to `calculator.py` and commit the
   change:

   ```python
   def subtract(a, b):
       return a - b
   ```

3. Switch back to `main` and merge `feature/subtract` into it with a merge
   commit (do not fast-forward the branch).

When you finish, leave `main` checked out.
