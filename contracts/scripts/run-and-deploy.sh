#!/bin/sh
# Boot a local Hardhat node, wait for it to accept JSON-RPC, deploy
# OpenDPPAnchor, then keep the node running in the foreground.
set -eu

echo "[run-and-deploy] starting hardhat node..."
pnpm exec hardhat node --hostname 0.0.0.0 &
NODE_PID=$!
trap "kill $NODE_PID 2>/dev/null" INT TERM

# Wait until JSON-RPC accepts a chain-id query (Node's net module — no wget needed).
echo "[run-and-deploy] waiting for JSON-RPC..."
i=0
while [ $i -lt 60 ]; do
    if node -e "
        const http = require('http');
        const req = http.request({
            host: 'localhost', port: 8545, method: 'POST', path: '/',
            headers: { 'content-type': 'application/json' },
        }, (res) => { res.on('data', () => {}); res.on('end', () => process.exit(0)); });
        req.on('error', () => process.exit(1));
        req.end(JSON.stringify({ jsonrpc: '2.0', method: 'eth_chainId', id: 1 }));
    " >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
    i=$((i + 1))
done

echo "[run-and-deploy] node is live; deploying OpenDPPAnchor..."
pnpm exec hardhat run scripts/deploy.ts --network localhost

echo "[run-and-deploy] deployment complete; node will keep running."
wait $NODE_PID
