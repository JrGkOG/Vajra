pragma solidity ^0.8.20;

contract VajraRegistry {

    struct FileAnchor {
        bytes32 merkleRoot;
        bytes32 manifestHash;
        address anchoredBy;
        uint32  totalChunks;
        uint64  anchoredAt;
        uint64  blockNumber;
        bool    revoked;
    }

    struct Checkpoint {
        bytes32 ledgerHead;
        address anchoredBy;
        uint64  seq;
        uint64  anchoredAt;
        uint64  blockNumber;
    }

    enum Verdict { NotAnchored, Match, Mismatch, Revoked, Compromised }

    enum Health { Unchecked, Healthy, Compromised }

    struct IntegrityRequest {
        bytes32 fileId;
        address requester;
        uint64  requestedAt;
        bool    fulfilled;
    }

    struct IntegrityReport {
        bytes32 observedRoot;
        address oracle;
        uint32  checks;
        uint64  reportedAt;
        uint64  blockNumber;
        Health  status;
    }

    address public owner;
    mapping(address => bool) public isAnchorer;

    mapping(bytes32 => FileAnchor) private anchors;
    Checkpoint[] private checkpoints;

    uint256 public totalFiles;

    mapping(address => bool) public isOracle;
    mapping(uint256 => IntegrityRequest) private requests;
    mapping(bytes32 => IntegrityReport) private reports;
    uint256 public requestCount;

    bytes1 private constant LEAF_PREFIX = 0x00;
    bytes1 private constant NODE_PREFIX = 0x01;

    event FileAnchored(
        bytes32 indexed fileId,
        bytes32 merkleRoot,
        bytes32 manifestHash,
        uint32 totalChunks,
        address indexed anchoredBy
    );
    event FileRevoked(bytes32 indexed fileId, bytes32 reasonHash, address indexed by);
    event CheckpointAnchored(
        uint256 indexed index,
        bytes32 ledgerHead,
        uint64 seq,
        address indexed anchoredBy
    );
    event AnchorerSet(address indexed account, bool allowed);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    event OracleSet(address indexed account, bool allowed);
    event IntegrityCheckRequested(
        uint256 indexed requestId, bytes32 indexed fileId, address indexed requester);
    event IntegrityReported(
        uint256 indexed requestId, bytes32 indexed fileId,
        Health status, bytes32 observedRoot, address indexed oracle);

    event TamperAlarm(
        bytes32 indexed fileId, bytes32 anchoredRoot, bytes32 observedRoot, address indexed oracle);

    error NotOwner();
    error NotAnchorer();
    error ZeroAddress();
    error EmptyCommitment();
    error AlreadyAnchored(bytes32 fileId);
    error NotAnchoredYet(bytes32 fileId);
    error AlreadyRevoked(bytes32 fileId);
    error CheckpointNotNewer(uint64 given, uint64 latest);
    error NoCheckpoint();
    error IndexOutOfRange();
    error NotOracle();
    error UnknownRequest(uint256 requestId);
    error AlreadyFulfilled(uint256 requestId);

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyAnchorer() {
        if (!isAnchorer[msg.sender]) revert NotAnchorer();
        _;
    }

    modifier onlyOracle() {
        if (!isOracle[msg.sender]) revert NotOracle();
        _;
    }

    constructor() {
        owner = msg.sender;
        isAnchorer[msg.sender] = true;
        emit OwnershipTransferred(address(0), msg.sender);
        emit AnchorerSet(msg.sender, true);
    }

    function setAnchorer(address account, bool allowed) external onlyOwner {
        if (account == address(0)) revert ZeroAddress();
        isAnchorer[account] = allowed;
        emit AnchorerSet(account, allowed);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function anchorFile(
        bytes32 fileId,
        bytes32 merkleRoot,
        bytes32 manifestHash,
        uint32 totalChunks
    ) external onlyAnchorer {
        if (merkleRoot == bytes32(0) || totalChunks == 0) revert EmptyCommitment();
        if (anchors[fileId].anchoredAt != 0) revert AlreadyAnchored(fileId);

        anchors[fileId] = FileAnchor({
            merkleRoot: merkleRoot,
            manifestHash: manifestHash,
            anchoredBy: msg.sender,
            totalChunks: totalChunks,
            anchoredAt: uint64(block.timestamp),
            blockNumber: uint64(block.number),
            revoked: false
        });
        unchecked { totalFiles += 1; }

        emit FileAnchored(fileId, merkleRoot, manifestHash, totalChunks, msg.sender);
    }

    function revokeFile(bytes32 fileId, bytes32 reasonHash) external onlyAnchorer {
        FileAnchor storage a = anchors[fileId];
        if (a.anchoredAt == 0) revert NotAnchoredYet(fileId);
        if (a.revoked) revert AlreadyRevoked(fileId);
        a.revoked = true;
        emit FileRevoked(fileId, reasonHash, msg.sender);
    }

    function anchorCheckpoint(bytes32 ledgerHead, uint64 seq) external onlyAnchorer {
        if (ledgerHead == bytes32(0)) revert EmptyCommitment();
        uint256 n = checkpoints.length;
        if (n > 0) {
            uint64 latest = checkpoints[n - 1].seq;
            if (seq <= latest) revert CheckpointNotNewer(seq, latest);
        }
        checkpoints.push(Checkpoint({
            ledgerHead: ledgerHead,
            anchoredBy: msg.sender,
            seq: seq,
            anchoredAt: uint64(block.timestamp),
            blockNumber: uint64(block.number)
        }));
        emit CheckpointAnchored(n, ledgerHead, seq, msg.sender);
    }

    function isAnchored(bytes32 fileId) external view returns (bool) {
        return anchors[fileId].anchoredAt != 0;
    }

    function getAnchor(bytes32 fileId) external view returns (FileAnchor memory) {
        FileAnchor memory a = anchors[fileId];
        if (a.anchoredAt == 0) revert NotAnchoredYet(fileId);
        return a;
    }

    function verifyFile(bytes32 fileId, bytes32 merkleRoot) external view returns (Verdict) {
        FileAnchor storage a = anchors[fileId];
        if (a.anchoredAt == 0) return Verdict.NotAnchored;
        if (a.revoked) return Verdict.Revoked;
        if (reports[fileId].status == Health.Compromised) return Verdict.Compromised;
        return a.merkleRoot == merkleRoot ? Verdict.Match : Verdict.Mismatch;
    }

    function verifyChunk(
        bytes32 fileId,
        bytes32 chunkHash,
        uint32 index,
        bytes32[] calldata proof
    ) external view returns (bool) {
        FileAnchor storage a = anchors[fileId];
        if (a.anchoredAt == 0 || a.revoked) return false;
        if (index >= a.totalChunks) return false;

        bytes32 node = leafHash(index, chunkHash);
        for (uint256 i = 0; i < proof.length; ) {
            node = nodeHash(node, proof[i]);
            unchecked { ++i; }
        }
        return node == a.merkleRoot;
    }

    function checkpointCount() external view returns (uint256) {
        return checkpoints.length;
    }

    function getCheckpoint(uint256 index) external view returns (Checkpoint memory) {
        if (index >= checkpoints.length) revert IndexOutOfRange();
        return checkpoints[index];
    }

    function latestCheckpoint() external view returns (Checkpoint memory) {
        uint256 n = checkpoints.length;
        if (n == 0) revert NoCheckpoint();
        return checkpoints[n - 1];
    }

    function setOracle(address account, bool allowed) external onlyOwner {
        if (account == address(0)) revert ZeroAddress();
        isOracle[account] = allowed;
        emit OracleSet(account, allowed);
    }

    function requestIntegrityCheck(bytes32 fileId) external onlyAnchorer returns (uint256 requestId) {
        if (anchors[fileId].anchoredAt == 0) revert NotAnchoredYet(fileId);
        unchecked { requestId = ++requestCount; }
        requests[requestId] = IntegrityRequest({
            fileId: fileId,
            requester: msg.sender,
            requestedAt: uint64(block.timestamp),
            fulfilled: false
        });
        emit IntegrityCheckRequested(requestId, fileId, msg.sender);
    }

    function fulfillIntegrityCheck(uint256 requestId, bytes32 observedRoot) external onlyOracle {
        IntegrityRequest storage r = requests[requestId];
        if (r.requestedAt == 0) revert UnknownRequest(requestId);
        if (r.fulfilled) revert AlreadyFulfilled(requestId);
        r.fulfilled = true;

        bytes32 fileId = r.fileId;
        bytes32 anchored = anchors[fileId].merkleRoot;
        Health verdict = (observedRoot == anchored) ? Health.Healthy : Health.Compromised;

        IntegrityReport storage rep = reports[fileId];
        rep.observedRoot = observedRoot;
        rep.oracle = msg.sender;
        rep.reportedAt = uint64(block.timestamp);
        rep.blockNumber = uint64(block.number);
        rep.status = verdict;
        unchecked { rep.checks += 1; }

        emit IntegrityReported(requestId, fileId, verdict, observedRoot, msg.sender);
        if (verdict == Health.Compromised) {
            emit TamperAlarm(fileId, anchored, observedRoot, msg.sender);
        }
    }

    function getIntegrityReport(bytes32 fileId) external view returns (IntegrityReport memory) {
        return reports[fileId];
    }

    function getRequest(uint256 requestId) external view returns (IntegrityRequest memory) {
        return requests[requestId];
    }

    function version() external pure returns (uint8) {
        return 2;
    }

    function leafHash(uint32 index, bytes32 chunkHash) public pure returns (bytes32) {
        return sha256(abi.encodePacked(LEAF_PREFIX, index, chunkHash));
    }

    function nodeHash(bytes32 a, bytes32 b) public pure returns (bytes32) {
        return a <= b
            ? sha256(abi.encodePacked(NODE_PREFIX, a, b))
            : sha256(abi.encodePacked(NODE_PREFIX, b, a));
    }
}
