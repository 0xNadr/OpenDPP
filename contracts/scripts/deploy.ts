/* eslint-disable no-console */
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

import hre from "hardhat";

async function main() {
  const factory = await hre.ethers.getContractFactory("OpenDPPAnchor");
  const contract = await factory.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  const deployer = (await contract.runner?.getAddress?.()) ?? "unknown";
  const networkName = hre.network.name;
  const chainId = Number(
    (await hre.ethers.provider.getNetwork()).chainId,
  );

  console.log(`OpenDPPAnchor deployed: ${address}`);
  console.log(`Network: ${networkName} (chainId=${chainId})`);
  console.log(`Deployer: ${deployer}`);

  // Persist deployment artifact so the API can find the address.
  const deployments = {
    network: networkName,
    chainId,
    address,
    deployer,
    deployedAt: new Date().toISOString(),
  };
  const outDir = join(__dirname, "..", "deployments");
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, `${networkName}.json`);
  writeFileSync(outPath, JSON.stringify(deployments, null, 2) + "\n");
  console.log(`Wrote deployment artifact: ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
