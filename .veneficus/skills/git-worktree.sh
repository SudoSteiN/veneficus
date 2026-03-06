#!/usr/bin/env bash
set -euo pipefail

# Git worktree management for parallel agent work.
# Usage: git-worktree.sh <command> [args]
#   create <branch>     — Create a worktree for the given branch
#   list                — List active worktrees
#   cleanup <branch>    — Remove a specific worktree
#   cleanup-all         — Remove all veneficus worktrees

WORKTREE_BASE="${CLAUDE_PROJECT_DIR:-.}/.worktrees"

case "${1:-help}" in
    create)
        BRANCH="${2:?Usage: git-worktree.sh create <branch-name>}"
        WORKTREE_PATH="$WORKTREE_BASE/$BRANCH"

        # Create branch if it doesn't exist
        if ! git show-ref --verify --quiet "refs/heads/$BRANCH" 2>/dev/null; then
            git branch "$BRANCH"
        fi

        mkdir -p "$WORKTREE_BASE"
        git worktree add "$WORKTREE_PATH" "$BRANCH"
        echo "$WORKTREE_PATH"
        ;;

    list)
        git worktree list
        ;;

    cleanup)
        BRANCH="${2:?Usage: git-worktree.sh cleanup <branch-name>}"
        WORKTREE_PATH="$WORKTREE_BASE/$BRANCH"

        if [ -d "$WORKTREE_PATH" ]; then
            git worktree remove "$WORKTREE_PATH" --force
            echo "Removed worktree: $WORKTREE_PATH"
        else
            echo "Worktree not found: $WORKTREE_PATH"
            exit 1
        fi
        ;;

    cleanup-all)
        if [ -d "$WORKTREE_BASE" ]; then
            for wt in "$WORKTREE_BASE"/*/; do
                [ -d "$wt" ] && git worktree remove "$wt" --force 2>/dev/null || true
            done
            rm -rf "$WORKTREE_BASE"
            echo "All worktrees cleaned up."
        else
            echo "No worktrees found."
        fi
        ;;

    help|*)
        echo "Usage: git-worktree.sh <command> [args]"
        echo "  create <branch>   — Create a worktree"
        echo "  list              — List worktrees"
        echo "  cleanup <branch>  — Remove a worktree"
        echo "  cleanup-all       — Remove all worktrees"
        ;;
esac
