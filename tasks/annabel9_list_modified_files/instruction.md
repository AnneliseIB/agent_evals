# List Modified Files

Fix `list_modified_files(repo_path)` in `/app/modified_files.py`.

Given a Git repository with at least one commit, return a sorted Python list of
repository-relative paths for tracked files with staged or unstaged edits.
Include each path only once, even if the file has both kinds of edits.
Exclude untracked files. A clean repository should return an empty list.

Preserve the function name and signature. Use only the Python standard library
and the installed Git command. Modify only `/app/modified_files.py`.
