// Retired proof transport. Intentionally has no imports, network, filesystem,
// worker or child-process behavior. No environment variable can re-enable it.
console.error(JSON.stringify({status:"remote_transport_disabled",
  reason:"out-of-host proof transport is prohibited; use the managed local compiler from an exact bound workspace. GitHub-hosted CI remains allowed."}));
process.exit(9);
