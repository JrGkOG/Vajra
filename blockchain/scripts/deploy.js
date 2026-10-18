// Deploys VajraRegistry and writes backend/chain_deployment.json so the
// FastAPI service knows the address + ABI without any manual copy/paste.
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const net = await hre.ethers.provider.getNetwork();

  console.log(`Network   : ${hre.network.name} (chainId ${net.chainId})`);
  console.log(`Deployer  : ${deployer.address}`);

  const Registry = await hre.ethers.getContractFactory("VajraRegistry");
  const registry = await Registry.deploy();
  const receipt = await registry.deploymentTransaction().wait();
  const address = await registry.getAddress();

  console.log(`Contract  : ${address}`);
  console.log(`Tx hash   : ${receipt.hash}`);
  console.log(`Block     : ${receipt.blockNumber}`);
  console.log(`Gas used  : ${receipt.gasUsed}`);

  // Authorise the oracle: a different wallet from the anchoring one, so no
  // single key can both write a commitment and vouch for it.
  const signers = await hre.ethers.getSigners();
  const oracleAddress =
    process.env.ORACLE_ADDRESS || (signers[1] ? signers[1].address : deployer.address);
  await (await registry.setOracle(oracleAddress, true)).wait();
  console.log(`Oracle    : ${oracleAddress}`);

  const artifact = await hre.artifacts.readArtifact("VajraRegistry");
  const out = {
    contract: "VajraRegistry",
    address,
    network: hre.network.name,
    chainId: Number(net.chainId),
    deployer: deployer.address,
    oracle: oracleAddress,
    txHash: receipt.hash,
    blockNumber: receipt.blockNumber,
    abi: artifact.abi,
  };

  const target = process.env.CHAIN_DEPLOYMENT
    || path.join(__dirname, "..", "..", "backend", "chain_deployment.json");
  fs.writeFileSync(target, JSON.stringify(out, null, 2));
  console.log(`Wrote     : ${path.relative(process.cwd(), target)}`);
}

main().catch((e) => { console.error(e); process.exitCode = 1; });
