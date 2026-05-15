import "@nomicfoundation/hardhat-toolbox";
import type { HardhatUserConfig } from "hardhat/config";

const AMOY_RPC_URL = process.env.AMOY_RPC_URL ?? "https://rpc-amoy.polygon.technology";
const DEPLOYER_PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY ?? "";

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    // Local Hardhat node — used by the docker-compose `hardhat` service.
    localhost: {
      url: "http://localhost:8545",
      chainId: 31337,
    },
    // Polygon Amoy testnet — set DEPLOYER_PRIVATE_KEY to deploy here.
    amoy: {
      url: AMOY_RPC_URL,
      chainId: 80002,
      accounts: DEPLOYER_PRIVATE_KEY ? [DEPLOYER_PRIVATE_KEY] : [],
    },
  },
};

export default config;
