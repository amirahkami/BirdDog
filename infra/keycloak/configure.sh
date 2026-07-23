#!/usr/bin/env bash
set -euo pipefail

readonly KCADM=/opt/keycloak/bin/kcadm.sh
readonly REALM=birddog
readonly ORGANIZATION_ID=00000000-0000-0000-0000-000000000001
readonly ADMIN_USER_ID=00000000-0000-0000-0000-000000000002

until "${KCADM}" config credentials \
  --server "${KEYCLOAK_INTERNAL_URL}" \
  --realm "${REALM}" \
  --client admin-cli \
  --user "${BIRDDOG_ADMIN_USERNAME}" \
  --password "${BIRDDOG_ADMIN_PASSWORD}" >/dev/null 2>&1 \
  && "${KCADM}" get \
    "organizations/${ORGANIZATION_ID}" \
    --realm "${REALM}" >/dev/null 2>&1; do
  sleep 2
done

if ! "${KCADM}" get \
  "organizations/${ORGANIZATION_ID}/members/${ADMIN_USER_ID}" \
  --realm "${REALM}" >/dev/null 2>&1; then
  "${KCADM}" create \
    "organizations/${ORGANIZATION_ID}/members" \
    --realm "${REALM}" \
    --body "\"${ADMIN_USER_ID}\"" >/dev/null
fi

echo "BirdDog realm is ready."
