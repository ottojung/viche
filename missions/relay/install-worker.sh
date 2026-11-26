#!/bin/sh
# Retired relay worker installer. Fails closed; installs nothing.
echo '{"status":"remote_transport_disabled","reason":"the relay worker is retired; no service is installed"}' >&2
exit 9
