# Viche execution environment. Build once, run as an unprivileged UID.
FROM node:22-bookworm

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates git jq gnupg openssh-client curl procps tzdata \
 && rm -rf /var/lib/apt/lists/*

# Use the same OpenCode CLI family required by the current Antonina runtime.
RUN npm install -g opencode-ai \
 && git clone --depth 1 https://github.com/ottojung/antonina.git /opt/antonina \
 && cd /opt/antonina \
 && npm run bootstrap \
 && npm run typecheck \
 && npm run pack:cli \
 && npm install -g ./antonina-cli-*.tgz

RUN groupadd -g 10001 viche \
 && useradd -u 10001 -g 10001 -m -s /bin/bash viche \
 && mkdir -p /home/viche/.config /home/viche/.local/state /home/viche/.local/share /home/viche/.cache /town /seats /constitution /founder \
 && chown -R viche:viche /home/viche /town /seats

ENV HOME=/home/viche \
    XDG_CONFIG_HOME=/home/viche/.config \
    XDG_STATE_HOME=/home/viche/.local/state \
    XDG_DATA_HOME=/home/viche/.local/share \
    XDG_CACHE_HOME=/home/viche/.cache \
    TZ=America/Vancouver

USER viche
WORKDIR /town
CMD ["bash", "/town/government/entrypoint.sh"]
