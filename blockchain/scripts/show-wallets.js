const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const file = process.env.CHAIN_DEPLOYMENT
    || path.join(__dirname, "..", "..", "backend", "chain_deployment.json");
  if (!fs.existsSync(file)) {
    throw new Error("No deployment found — start the backend first so it deploys the contract.");
  }
  const dep = JSON.parse(fs.readFileSync(file, "utf8"));
  const registry = await hre.ethers.getContractAt("VajraRegistry", dep.address);
  const net = await hre.ethers.provider.getNetwork();
  const block = await hre.ethers.provider.getBlockNumber();
  const owner = await registry.owner();

  console.log("=".repeat(86));
  console.log(` LOCAL CHAIN WALLETS   chain id ${net.chainId}   latest block #${block}`);
  console.log(` Contract: ${dep.address}`);
  console.log("=".repeat(86));
  console.log(" #   ADDRESS                                     BALANCE     TXS  ROLE");
  console.log("-".repeat(86));

  const signers = await hre.ethers.getSigners();
  for (let i = 0; i < 4; i++) {
    const a = signers[i].address;
    const bal = hre.ethers.formatEther(await hre.ethers.provider.getBalance(a));
    const txs = await hre.ethers.provider.getTransactionCount(a);
    const roles = [];
    if (a === owner) roles.push("OWNER");
    if (await registry.isAnchorer(a)) roles.push("ANCHORER");
    if (await registry.isOracle(a)) roles.push("ORACLE");
    console.log(
      ` ${i}   ${a}   ${Number(bal).toFixed(4).padStart(14)}   ${String(txs).padStart(4)}  ${roles.join(" + ") || "-"}`
    );
  }
  console.log("-".repeat(86));
  console.log(" Accounts #4-#19 also exist, each funded with 10000 fake ETH and holding no role.");
  console.log(" Balances drop slightly with every transaction: that is the gas fee.");
  console.log("=".repeat(86));
}

main().catch((e) => { console.error(e.message); process.exitCode = 1; });
