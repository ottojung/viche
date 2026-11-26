#!/bin/sh
# Retired relay client installer. Fails closed; installs nothing.
#
# The former wrappers pointed at out-of-host proof transport, which is now
# prohibited. Local role dispatch remains available directly from
# missions/pnp/role_prompt.py and does not require this installer.
echo '{"status":"remote_transport_disabled","reason":"the relay installer is retired; no client is installed"}' >&2
exit 9
