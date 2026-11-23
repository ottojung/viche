#!/bin/sh
# POSIX git credential helper.  Feeds the fine-grained fork token to git on
# stdout only when git asks for it; never logs, echoes or exports it.
set -eu
case "${1:-}" in
  get)
    printf 'username=%s\n' 'x-access-token'
    printf 'password=%s\n' "$(tr -d '\r\n' < "$HOME/.config/viche-pequalnp/token")"
    ;;
esac
exit 0
