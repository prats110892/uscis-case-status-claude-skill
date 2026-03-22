#!/bin/bash
# USCIS Case Status -- Uninstall
# Run from your Claude Code project root: bash uninstall.sh

PROJECT_ROOT="$(pwd)"

echo ""
echo "  Removing USCIS Case Status skill..."

# Remove skill
if [ -d "$PROJECT_ROOT/.claude/skills/uscis-case-status" ]; then
    rm -rf "$PROJECT_ROOT/.claude/skills/uscis-case-status"
    echo "  ✓ Removed .claude/skills/uscis-case-status"
else
    echo "  - Skill directory not found, skipping"
fi

# Remove script
if [ -f "$PROJECT_ROOT/scripts/uscis_check.py" ]; then
    rm "$PROJECT_ROOT/scripts/uscis_check.py"
    echo "  ✓ Removed scripts/uscis_check.py"
else
    echo "  - scripts/uscis_check.py not found, skipping"
fi

# Strip USCIS credentials from .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    grep -v "^USCIS_" "$PROJECT_ROOT/.env" > "$PROJECT_ROOT/.env.tmp" && mv "$PROJECT_ROOT/.env.tmp" "$PROJECT_ROOT/.env"
    echo "  ✓ Removed USCIS credentials from .env"
fi

echo ""
echo "  Done. To reinstall, run: python3 setup.py"
echo ""
