#!/bin/sh
set -eu
[ "$(hostname)" = marceline-dev ] || { echo 'worker installation is marceline-dev only' >&2; exit 1; }
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$src/install.sh"
name=marceline-relay
mkdir -p "/etc/services.d/$name" "/run/s6/legacy-services/$name"
for dir in "/etc/services.d/$name" "/run/s6/legacy-services/$name"; do
  cp "$src/service-run" "$dir/run.tmp"
  chmod 755 "$dir/run.tmp"
  mv "$dir/run.tmp" "$dir/run"
done
if [ ! -e "/run/service/$name" ]; then
  ln -s "/run/s6/legacy-services/$name" "/run/service/$name"
fi
/command/s6-svscanctl -a /run/service
if /command/s6-svstat "/run/service/$name" >/dev/null 2>&1; then
  /command/s6-svc -r "/run/service/$name"
fi
