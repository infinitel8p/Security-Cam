#!/bin/bash
# Run once after cloning to enable the version-bump pre-commit hook.
git config core.hooksPath hooks
echo "Git hooks path set to ./hooks"
