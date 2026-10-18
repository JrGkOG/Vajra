const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const vectors = require("./fixtures/merkle_vectors.json");

// Mirrors backend/ledger.py file_key(): sha256 of the UUID string.
const fileKey = (uuid) => ethers.sha256(ethers.toUtf8Bytes(uuid));
const H = (s) => ethers.sha256(ethers.toUtf8Bytes(s));

const Verdict = { NotAnchored: 0n, Match: 1n, Mismatch: 2n, Revoked: 3n, Compromised: 4n };

describe("VajraRegistry", () => {
  async function deploy() {
    const [owner, api, stranger] = await ethers.getSigners();
    const registry = await (await ethers.getContractFactory("VajraRegistry")).deploy();
    await registry.setAnchorer(api.address, true);
    return { registry, owner, api, stranger };
  }

  const FILE = fileKey("11111111-2222-3333-4444-555555555555");
  const ROOT = H("root");
  const MANIFEST = H("manifest");

  describe("roles", () => {
    it("deployer is owner and anchorer", async () => {
      const { registry, owner } = await loadFixture(deploy);
      expect(await registry.owner()).to.equal(owner.address);
      expect(await registry.isAnchorer(owner.address)).to.equal(true);
    });

    it("a stranger cannot anchor", async () => {
      const { registry, stranger } = await loadFixture(deploy);
      await expect(registry.connect(stranger).anchorFile(FILE, ROOT, MANIFEST, 4))
        .to.be.revertedWithCustomError(registry, "NotAnchorer");
    });

    it("only the owner manages the anchorer roster", async () => {
      const { registry, api, stranger } = await loadFixture(deploy);
      await expect(registry.connect(api).setAnchorer(stranger.address, true))
        .to.be.revertedWithCustomError(registry, "NotOwner");
    });

    it("a de-authorised anchorer loses write access", async () => {
      const { registry, api } = await loadFixture(deploy);
      await registry.setAnchorer(api.address, false);
      await expect(registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 4))
        .to.be.revertedWithCustomError(registry, "NotAnchorer");
    });

    it("ownership transfers and the old owner loses control", async () => {
      const { registry, owner, stranger } = await loadFixture(deploy);
      await expect(registry.transferOwnership(stranger.address))
        .to.emit(registry, "OwnershipTransferred").withArgs(owner.address, stranger.address);
      await expect(registry.setAnchorer(owner.address, false))
        .to.be.revertedWithCustomError(registry, "NotOwner");
    });

    it("rejects the zero address", async () => {
      const { registry } = await loadFixture(deploy);
      await expect(registry.transferOwnership(ethers.ZeroAddress))
        .to.be.revertedWithCustomError(registry, "ZeroAddress");
    });
  });

  describe("file anchoring", () => {
    it("stores the commitment and emits FileAnchored", async () => {
      const { registry, api } = await loadFixture(deploy);
      await expect(registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 7))
        .to.emit(registry, "FileAnchored").withArgs(FILE, ROOT, MANIFEST, 7, api.address);

      const a = await registry.getAnchor(FILE);
      expect(a.merkleRoot).to.equal(ROOT);
      expect(a.manifestHash).to.equal(MANIFEST);
      expect(a.totalChunks).to.equal(7n);
      expect(a.anchoredBy).to.equal(api.address);
      expect(a.revoked).to.equal(false);
      expect(await registry.totalFiles()).to.equal(1n);
    });

    it("is write-once: a second anchor for the same file reverts", async () => {
      const { registry, api } = await loadFixture(deploy);
      await registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 7);
      await expect(registry.connect(api).anchorFile(FILE, H("doctored"), MANIFEST, 7))
        .to.be.revertedWithCustomError(registry, "AlreadyAnchored");
      expect((await registry.getAnchor(FILE)).merkleRoot).to.equal(ROOT);
    });

    it("rejects empty commitments", async () => {
      const { registry, api } = await loadFixture(deploy);
      await expect(registry.connect(api).anchorFile(FILE, ethers.ZeroHash, MANIFEST, 7))
        .to.be.revertedWithCustomError(registry, "EmptyCommitment");
      await expect(registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 0))
        .to.be.revertedWithCustomError(registry, "EmptyCommitment");
    });

    it("verifyFile returns the right verdict", async () => {
      const { registry, api } = await loadFixture(deploy);
      expect(await registry.verifyFile(FILE, ROOT)).to.equal(Verdict.NotAnchored);
      await registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 3);
      expect(await registry.verifyFile(FILE, ROOT)).to.equal(Verdict.Match);
      expect(await registry.verifyFile(FILE, H("tampered"))).to.equal(Verdict.Mismatch);
      await registry.connect(api).revokeFile(FILE, H("compromised"));
      expect(await registry.verifyFile(FILE, ROOT)).to.equal(Verdict.Revoked);
    });

    it("revocation flags but never erases the anchor", async () => {
      const { registry, api } = await loadFixture(deploy);
      await registry.connect(api).anchorFile(FILE, ROOT, MANIFEST, 3);
      await expect(registry.connect(api).revokeFile(FILE, H("why")))
        .to.emit(registry, "FileRevoked");
      expect((await registry.getAnchor(FILE)).merkleRoot).to.equal(ROOT);
      await expect(registry.connect(api).revokeFile(FILE, H("why")))
        .to.be.revertedWithCustomError(registry, "AlreadyRevoked");
    });

    it("cannot revoke an unknown file", async () => {
      const { registry, api } = await loadFixture(deploy);
      await expect(registry.connect(api).revokeFile(FILE, H("x")))
        .to.be.revertedWithCustomError(registry, "NotAnchoredYet");
    });
  });

  describe("Merkle proofs (vectors generated by Python backend/ledger.py)", () => {
    for (const c of vectors.cases) {
      it(`accepts every chunk proof for a ${c.n}-chunk file`, async () => {
        const { registry, api } = await loadFixture(deploy);
        const id = fileKey(`file-${c.n}`);
        await registry.connect(api).anchorFile(id, c.root, MANIFEST, c.n);
        expect(await registry.verifyFile(id, c.root)).to.equal(Verdict.Match);

        for (let i = 0; i < c.n; i++) {
          expect(await registry.verifyChunk(id, c.chunkHashes[i], i, c.proofs[i])).to.equal(true);
        }
      });
    }

    it("rejects a tampered chunk, a wrong position and an out-of-range index", async () => {
      const { registry, api } = await loadFixture(deploy);
      const c = vectors.cases.find((v) => v.n === 8);
      const id = fileKey("file-8");
      await registry.connect(api).anchorFile(id, c.root, MANIFEST, c.n);

      expect(await registry.verifyChunk(id, H("evil"), 3, c.proofs[3])).to.equal(false);
      expect(await registry.verifyChunk(id, c.chunkHashes[3], 4, c.proofs[3])).to.equal(false);
      expect(await registry.verifyChunk(id, c.chunkHashes[3], 99, c.proofs[3])).to.equal(false);
    });

    it("leaf and node hashes are domain-separated", async () => {
      const { registry } = await loadFixture(deploy);
      const x = H("x");
      expect(await registry.leafHash(0, x)).to.not.equal(await registry.nodeHash(x, x));
    });
  });

  describe("audit-ledger checkpoints", () => {
    it("records heads and exposes the latest", async () => {
      const { registry, api } = await loadFixture(deploy);
      await expect(registry.latestCheckpoint()).to.be.revertedWithCustomError(registry, "NoCheckpoint");

      await expect(registry.connect(api).anchorCheckpoint(H("head-10"), 10))
        .to.emit(registry, "CheckpointAnchored").withArgs(0, H("head-10"), 10, api.address);
      await registry.connect(api).anchorCheckpoint(H("head-25"), 25);

      expect(await registry.checkpointCount()).to.equal(2n);
      const latest = await registry.latestCheckpoint();
      expect(latest.ledgerHead).to.equal(H("head-25"));
      expect(latest.seq).to.equal(25n);
    });

    it("is append-only: the sequence can never move backwards or repeat", async () => {
      const { registry, api } = await loadFixture(deploy);
      await registry.connect(api).anchorCheckpoint(H("a"), 20);
      await expect(registry.connect(api).anchorCheckpoint(H("b"), 20))
        .to.be.revertedWithCustomError(registry, "CheckpointNotNewer");
      await expect(registry.connect(api).anchorCheckpoint(H("c"), 5))
        .to.be.revertedWithCustomError(registry, "CheckpointNotNewer");
    });

    it("bounds-checks historical lookups", async () => {
      const { registry } = await loadFixture(deploy);
      await expect(registry.getCheckpoint(0)).to.be.revertedWithCustomError(registry, "IndexOutOfRange");
    });
  });
});

// ───────────────────────────── oracle ─────────────────────────────
describe("VajraRegistry oracle (request / callback)", () => {
  async function setup() {
    const [owner, api, oracle, stranger] = await ethers.getSigners();
    const registry = await (await ethers.getContractFactory("VajraRegistry")).deploy();
    await registry.setAnchorer(api.address, true);
    await registry.setOracle(oracle.address, true);
    const file = fileKey("oracle-file");
    const root = H("anchored-root");
    await registry.connect(api).anchorFile(file, root, H("manifest"), 4);
    return { registry, owner, api, oracle, stranger, file, root };
  }

  it("reports its version so a stale deployment can be detected", async () => {
    const { registry } = await loadFixture(setup);
    expect(await registry.version()).to.equal(2n);
  });

  it("only the owner manages oracles", async () => {
    const { registry, api, stranger } = await loadFixture(setup);
    await expect(registry.connect(api).setOracle(stranger.address, true))
      .to.be.revertedWithCustomError(registry, "NotOwner");
    await expect(registry.setOracle(ethers.ZeroAddress, true))
      .to.be.revertedWithCustomError(registry, "ZeroAddress");
  });

  it("request emits an event with an incrementing id", async () => {
    const { registry, api, file } = await loadFixture(setup);
    await expect(registry.connect(api).requestIntegrityCheck(file))
      .to.emit(registry, "IntegrityCheckRequested").withArgs(1, file, api.address);
    await expect(registry.connect(api).requestIntegrityCheck(file))
      .to.emit(registry, "IntegrityCheckRequested").withArgs(2, file, api.address);
    expect(await registry.requestCount()).to.equal(2n);
  });

  it("cannot request a check on an unanchored file, or as a stranger", async () => {
    const { registry, api, stranger, file } = await loadFixture(setup);
    await expect(registry.connect(api).requestIntegrityCheck(fileKey("nope")))
      .to.be.revertedWithCustomError(registry, "NotAnchoredYet");
    await expect(registry.connect(stranger).requestIntegrityCheck(file))
      .to.be.revertedWithCustomError(registry, "NotAnchorer");
  });

  it("a matching observation is recorded as Healthy", async () => {
    const { registry, api, oracle, file, root } = await loadFixture(setup);
    await registry.connect(api).requestIntegrityCheck(file);
    await expect(registry.connect(oracle).fulfillIntegrityCheck(1, root))
      .to.emit(registry, "IntegrityReported").withArgs(1, file, 1, root, oracle.address)
      .and.not.to.emit(registry, "TamperAlarm");

    const rep = await registry.getIntegrityReport(file);
    expect(rep.status).to.equal(1n);          // Healthy
    expect(rep.oracle).to.equal(oracle.address);
    expect(rep.checks).to.equal(1n);
    expect(await registry.verifyFile(file, root)).to.equal(Verdict.Match);
  });

  it("a differing observation raises TamperAlarm and flips verifyFile", async () => {
    const { registry, api, oracle, file, root } = await loadFixture(setup);
    const seen = H("what-storage-actually-contains");
    await registry.connect(api).requestIntegrityCheck(file);
    await expect(registry.connect(oracle).fulfillIntegrityCheck(1, seen))
      .to.emit(registry, "TamperAlarm").withArgs(file, root, seen, oracle.address);

    expect((await registry.getIntegrityReport(file)).status).to.equal(2n);   // Compromised
    // Even the *correct* root no longer verifies: the contract enforces the finding.
    expect(await registry.verifyFile(file, root)).to.equal(Verdict.Compromised);
  });

  it("a later clean check clears the flag, and history stays in the events", async () => {
    const { registry, api, oracle, file, root } = await loadFixture(setup);
    await registry.connect(api).requestIntegrityCheck(file);
    await registry.connect(oracle).fulfillIntegrityCheck(1, H("bad"));
    await registry.connect(api).requestIntegrityCheck(file);
    await registry.connect(oracle).fulfillIntegrityCheck(2, root);

    const rep = await registry.getIntegrityReport(file);
    expect(rep.status).to.equal(1n);
    expect(rep.checks).to.equal(2n);
    const alarms = await registry.queryFilter(registry.filters.TamperAlarm());
    expect(alarms.length).to.equal(1);        // the alarm is permanent
  });

  it("only an oracle can fulfil — not the anchorer, not the owner", async () => {
    const { registry, owner, api, file, root } = await loadFixture(setup);
    await registry.connect(api).requestIntegrityCheck(file);
    await expect(registry.connect(api).fulfillIntegrityCheck(1, root))
      .to.be.revertedWithCustomError(registry, "NotOracle");
    await expect(registry.connect(owner).fulfillIntegrityCheck(1, root))
      .to.be.revertedWithCustomError(registry, "NotOracle");
  });

  it("a request can be fulfilled once, and unknown ids revert", async () => {
    const { registry, api, oracle, file, root } = await loadFixture(setup);
    await registry.connect(api).requestIntegrityCheck(file);
    await registry.connect(oracle).fulfillIntegrityCheck(1, root);
    await expect(registry.connect(oracle).fulfillIntegrityCheck(1, root))
      .to.be.revertedWithCustomError(registry, "AlreadyFulfilled");
    await expect(registry.connect(oracle).fulfillIntegrityCheck(99, root))
      .to.be.revertedWithCustomError(registry, "UnknownRequest");
  });

  it("a de-authorised oracle can no longer report", async () => {
    const { registry, api, oracle, file, root } = await loadFixture(setup);
    await registry.connect(api).requestIntegrityCheck(file);
    await registry.setOracle(oracle.address, false);
    await expect(registry.connect(oracle).fulfillIntegrityCheck(1, root))
      .to.be.revertedWithCustomError(registry, "NotOracle");
  });
});
