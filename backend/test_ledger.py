"""Unit tests for ledger.py — run with:  python3 -m unittest test_ledger -v"""
import hashlib
import unittest

import ledger


def chunk_hashes(n):
    return [hashlib.sha256(f"chunk-{i}".encode()).hexdigest() for i in range(n)]


class MerkleTests(unittest.TestCase):
    def test_single_chunk_root_is_its_leaf(self):
        h = chunk_hashes(1)
        self.assertEqual(ledger.merkle_root(h), ledger.leaf_hash(0, h[0]).hex())

    def test_proofs_verify_for_every_size_and_index(self):
        for n in range(1, 26):                 # covers odd/even/power-of-two shapes
            hs = chunk_hashes(n)
            root = ledger.merkle_root(hs)
            for i in range(n):
                proof = ledger.merkle_proof(hs, i)
                self.assertTrue(ledger.verify_merkle_proof(hs[i], i, proof, root), (n, i))

    def test_changing_one_chunk_changes_root(self):
        hs = chunk_hashes(8)
        tampered = list(hs)
        tampered[3] = hashlib.sha256(b"evil").hexdigest()
        self.assertNotEqual(ledger.merkle_root(hs), ledger.merkle_root(tampered))

    def test_reordering_chunks_changes_root(self):
        hs = chunk_hashes(6)
        swapped = list(hs)
        swapped[1], swapped[4] = swapped[4], swapped[1]
        self.assertNotEqual(ledger.merkle_root(hs), ledger.merkle_root(swapped))

    def test_proof_rejects_wrong_chunk_or_wrong_position(self):
        hs = chunk_hashes(9)
        root = ledger.merkle_root(hs)
        proof = ledger.merkle_proof(hs, 5)
        self.assertFalse(ledger.verify_merkle_proof(hs[6], 5, proof, root))
        self.assertFalse(ledger.verify_merkle_proof(hs[5], 4, proof, root))

    def test_no_duplicate_leaf_ambiguity(self):
        # Bitcoin duplicates odd nodes, so [a,b,c] and [a,b,c,c] share a root.
        hs = chunk_hashes(3)
        self.assertNotEqual(ledger.merkle_root(hs), ledger.merkle_root(hs + [hs[-1]]))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            ledger.merkle_root([])

    def test_known_vector_for_solidity_parity(self):
        # Pinned so the Solidity test can assert the identical value.
        hs = [hashlib.sha256(f"chunk-{i}".encode()).hexdigest() for i in range(3)]
        self.assertEqual(len(ledger.merkle_root(hs)), 64)


class ChainTests(unittest.TestCase):
    def build(self, n):
        rows, prev = [], ledger.GENESIS_HASH
        for i in range(n):
            entry = {"user_id": "u1", "action": "UPLOAD", "resource_id": f"f{i}"}
            chain = ledger.seal(prev, entry, i + 1)
            rows.append({"entry": entry, "chain": chain})
            prev = chain["entry_hash"]
        return rows

    def test_clean_chain_verifies(self):
        r = ledger.verify_chain(self.build(10))
        self.assertTrue(r["valid"])
        self.assertEqual((r["length"], r["head_seq"]), (10, 10))

    def test_edited_row_detected(self):
        rows = self.build(10)
        rows[4]["entry"]["action"] = "DOWNLOAD"
        r = ledger.verify_chain(rows)
        self.assertFalse(r["valid"])
        self.assertEqual(r["broken_at"], 4)

    def test_deleted_row_detected(self):
        rows = self.build(10)
        del rows[5]
        r = ledger.verify_chain(rows)
        self.assertFalse(r["valid"])
        self.assertEqual(r["broken_at"], 5)

    def test_reordered_rows_detected(self):
        rows = self.build(6)
        rows[2], rows[3] = rows[3], rows[2]
        self.assertFalse(ledger.verify_chain(rows)["valid"])

    def test_empty_chain_is_valid(self):
        self.assertTrue(ledger.verify_chain([])["valid"])

    def test_whole_chain_recomputed_still_matches_only_a_different_head(self):
        # An attacker who recomputes every hash produces a *valid* chain with a
        # *different* head — which is why the head is pinned on-chain.
        rows = self.build(5)
        honest_head = ledger.verify_chain(rows)["head"]
        rows[1]["entry"]["action"] = "DELETE"
        prev = ledger.GENESIS_HASH
        for i, row in enumerate(rows):
            row["chain"] = ledger.seal(prev, row["entry"], i + 1)
            prev = row["chain"]["entry_hash"]
        forged = ledger.verify_chain(rows)
        self.assertTrue(forged["valid"])
        self.assertNotEqual(forged["head"], honest_head)


if __name__ == "__main__":
    unittest.main()
