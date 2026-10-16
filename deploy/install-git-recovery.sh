#!/bin/sh
# Install the viche-git-recovery S6 service (parliament-controlled, out-of-loop).
# The recovery scripts live in the town checkout's government/ tree (like
# intake-watch.sh) and stay readable even while the checkout is conflicted,
# which is exactly when recovery must run. Follows the sentinel installer
# pattern: write the run script atomically, then activate via s6-svscanctl.
set -eu
: "${VICHE_TOWNHALL_ID:?Host Town Hall ID required}"
services=${VICHE_RECOVERY_SERVICES:-/etc/services.d}
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
mkdir -p "$services/viche-git-recovery"
{
    printf '#!/bin/sh\nexport VICHE_TOWNHALL_ID=%s\n' "$VICHE_TOWNHALL_ID"
    sed '1d' "$here/s6/viche-git-recovery/run"
} >"$services/viche-git-recovery/run.next"
chmod 0755 "$services/viche-git-recovery/run.next"
mv -f "$services/viche-git-recovery/run.next" "$services/viche-git-recovery/run"
printf 'Installed viche-git-recovery service (Town Hall %s)\n' "$VICHE_TOWNHALL_ID"
printf 'Activate with: ln -s %s/viche-git-recovery /run/service/viche-git-recovery && s6-svscanctl -a /run/service\n' "$services"
