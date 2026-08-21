#!/usr/bin/env bash
# ABOUTME: Installs agent skills by symlinking each SKILL.md directory into agent skill paths.
# ABOUTME: Works inside a clone, or piped from curl, in which case it clones the repo first.

set -euo pipefail

REPO_URL="${AGENT_SKILLS_REPO:-https://github.com/kwajiehao/agent-skills.git}"
CLONE_DIR="${AGENT_SKILLS_DIR:-$HOME/.agent-skills}"

# Claude Code always gets a link. Codex and the generic agents path are only
# populated when their config directory already exists, so we don't scatter
# empty directories for tools that aren't installed.
ALWAYS_TARGETS=("$HOME/.claude/skills")
OPTIONAL_TARGETS=("$HOME/.codex/skills" "$HOME/.agents/skills")

die() { printf 'error: %s\n' "$1" >&2; exit 1; }

# Absolute directory containing this script, resolving symlinks. Fails when the
# script is piped (no BASH_SOURCE), which is how we detect bootstrap mode.
script_dir() {
    local src="${BASH_SOURCE[0]:-}"
    [ -n "$src" ] || return 1
    while [ -L "$src" ]; do
        local dir
        dir="$(cd -P "$(dirname "$src")" && pwd)"
        src="$(readlink "$src")"
        case "$src" in /*) ;; *) src="$dir/$src" ;; esac
    done
    (cd -P "$(dirname "$src")" && pwd)
}

resolve_repo() {
    local dir
    if dir="$(script_dir 2>/dev/null)" && [ -f "$dir/install.sh" ]; then
        printf '%s' "$dir"
        return
    fi

    # Piped from curl: fetch the repo, then install from the clone.
    command -v git >/dev/null 2>&1 || die "git is required"
    if [ -d "$CLONE_DIR/.git" ]; then
        printf 'Updating existing clone at %s\n' "$CLONE_DIR" >&2
        git -C "$CLONE_DIR" pull --ff-only --quiet \
            || printf '  [warn] pull failed; installing the checkout as-is\n' >&2
    else
        printf 'Cloning %s into %s\n' "$REPO_URL" "$CLONE_DIR" >&2
        git clone --depth 1 --quiet "$REPO_URL" "$CLONE_DIR" || die "clone failed"
    fi
    printf '%s' "$CLONE_DIR"
}

link_into() {
    local target_dir="$1" installed=0 skipped=0 relinked=0
    mkdir -p "$target_dir"

    local skill_dir skill_name dest current
    for skill_dir in "$REPO_DIR"/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        skill_name="$(basename "$skill_dir")"
        dest="$target_dir/$skill_name"
        skill_dir="${skill_dir%/}"

        if [ -L "$dest" ]; then
            current="$(readlink "$dest")"
            if [ "$current" = "$skill_dir" ]; then
                printf '  [skip] %s (already linked)\n' "$skill_name"
                skipped=$((skipped + 1))
            elif [ ! -e "$dest" ]; then
                # Dangling link from a moved or deleted clone: safe to repair.
                ln -sfn "$skill_dir" "$dest"
                printf '  [fix]  %s (was dangling -> %s)\n' "$skill_name" "$current"
                relinked=$((relinked + 1))
            else
                printf '  [warn] %s points to %s; leaving it alone\n' "$skill_name" "$current"
                skipped=$((skipped + 1))
            fi
            continue
        fi

        if [ -e "$dest" ]; then
            printf '  [warn] %s exists and is not a symlink; leaving it alone\n' "$skill_name"
            skipped=$((skipped + 1))
            continue
        fi

        ln -s "$skill_dir" "$dest"
        printf '  [ok]   %s\n' "$skill_name"
        installed=$((installed + 1))
    done

    printf '  linked %d, repaired %d, skipped %d\n' "$installed" "$relinked" "$skipped"
}

REPO_DIR="$(resolve_repo)"
[ -n "$(find "$REPO_DIR" -mindepth 2 -maxdepth 2 -name SKILL.md -print -quit)" ] \
    || die "no skills found in $REPO_DIR"

for target in "${ALWAYS_TARGETS[@]}"; do
    printf '\n=== %s ===\n' "$target"
    link_into "$target"
done

for target in "${OPTIONAL_TARGETS[@]}"; do
    if [ -d "$(dirname "$target")" ]; then
        printf '\n=== %s ===\n' "$target"
        link_into "$target"
    fi
done

printf '\nInstalled skills:\n'
for skill_dir in "$REPO_DIR"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    desc="$(awk '/^---$/{n++; next} n==1 && /^description:/{sub(/^description:[[:space:]]*/, ""); print; exit}' "$skill_dir/SKILL.md")"
    printf '  /%s — %s\n' "$(basename "$skill_dir")" "${desc:-no description}"
done

printf '\nRestart Claude Code (or run /skills) to pick up new skills.\n'
