require("@nomicfoundation/hardhat-toolbox");

// Optional: copy .env.example to .env to deploy to a public testnet.
// Local development needs none of this.
const { SEPOLIA_RPC_URL, DEPLOYER_PRIVATE_KEY } = process.env;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    // `hardhat node` prints every RPC call by default; the oracle polls constantly.
    hardhat: { loggingEnabled: false },
    // `npx hardhat node` — a local single-node EVM chain with 20 funded accounts.
    localhost: { url: process.env.CHAIN_RPC_URL || "http://127.0.0.1:8545" },
    ...(SEPOLIA_RPC_URL && DEPLOYER_PRIVATE_KEY
      ? { sepolia: { url: SEPOLIA_RPC_URL, accounts: [DEPLOYER_PRIVATE_KEY] } }
      : {}),
  },
};
