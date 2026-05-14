# autograde

A Python CLI tool that validates repository requirements:

1. Repository is a valid git repository.
2. Repository has a `main` branch.
3. Repository has a `feature` branch on the remote.
4. `file1.txt` exists in the `main` branch.

## Usage

```bash
uv run autograde <repository-url>
```

Pass `--json` to print machine-readable output.
