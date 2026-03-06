#!/usr/bin/env bash
set -euo pipefail

# State capture for rollback points.
# Creates lightweight git snapshots without polluting branch history.
# Usage: snapshot.sh <command> [args]
#   save [message]   — Create a snapshot (stash-like)
#   list             — List snapshots
#   restore <ref>    — Restore a snapshot
#   diff <ref>       — Show changes since snapshot

SNAPSHOT_PREFIX="veneficus-snapshot"

case "${1:-help}" in
    save)
        MESSAGE="${2:-auto-snapshot $(date +%H:%M:%S)}"
        # Create a commit on a detached ref (doesn't affect branches)
        TREE=$(git write-tree)
        PARENT=$(git rev-parse HEAD)
        COMMIT=$(echo "$MESSAGE" | git commit-tree "$TREE" -p "$PARENT")
        git update-ref "refs/$SNAPSHOT_PREFIX/$(date +%Y%m%d-%H%M%S)" "$COMMIT"
        echo "Snapshot saved: $COMMIT (${MESSAGE})"
        ;;

    list)
        echo "Snapshots:"
        git for-each-ref --sort=-creatordate "refs/$SNAPSHOT_PREFIX/" \
            --format='  %(refname:short) %(creatordate:relative) — %(subject)' \
            2>/dev/null || echo "  (none)"
        ;;

    restore)
        REF="${2:?Usage: snapshot.sh restore <ref>}"
        # Find the ref
        FULL_REF=$(git for-each-ref --format='%(refname)' "refs/$SNAPSHOT_PREFIX/" | grep "$REF" | head -1)
        if [ -z "$FULL_REF" ]; then
            echo "Snapshot not found: $REF" >&2
            exit 1
        fi
        git read-tree "$FULL_REF"
        git checkout-index -a -f
        echo "Restored snapshot: $FULL_REF"
        ;;

    diff)
        REF="${2:?Usage: snapshot.sh diff <ref>}"
        FULL_REF=$(git for-each-ref --format='%(refname)' "refs/$SNAPSHOT_PREFIX/" | grep "$REF" | head -1)
        if [ -z "$FULL_REF" ]; then
            echo "Snapshot not found: $REF" >&2
            exit 1
        fi
        git diff "$FULL_REF" HEAD
        ;;

    help|*)
        echo "Usage: snapshot.sh <command> [args]"
        echo "  save [message]  — Create a rollback point"
        echo "  list            — List snapshots"
        echo "  restore <ref>   — Restore a snapshot"
        echo "  diff <ref>      — Show changes since snapshot"
        ;;
esac
