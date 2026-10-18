"""Tests for chain_journal.py — run with:  python3 -m unittest test_chain_journal -v"""
import os
import tempfile
import unittest
from pathlib import Path

import chain_journal


class FakeChain:
    """Stands in for ChainService so replay logic is tested without a node."""
    def __init__(self, anchored=(), latest_seq=0):
        self.anchored, self.latest_seq = set(anchored), latest_seq
        self.file_calls, self.cp_calls = [], []

    def _latest_checkpoint_sync(self):
        return {"seq": self.latest_seq} if self.latest_seq else None

    def _is_anchored_sync(self, file_id):
        return file_id in self.anchored

    def _anchor_file_sync(self, file_id, root, manifest, n, journal=True):
        assert journal is False, "replay must not re-journal"
        self.anchored.add(file_id); self.file_calls.append(file_id)

    def _anchor_checkpoint_sync(self, head, seq, journal=True):
        assert journal is False
        self.latest_seq = seq; self.cp_calls.append(seq)


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.environ["CHAIN_JOURNAL"] = str(Path(self.dir.name) / "j.jsonl")

    def tearDown(self):
        os.environ.pop("CHAIN_JOURNAL", None)
        self.dir.cleanup()

    def fill(self):
        chain_journal.append({"type": "file", "file_id": "a", "merkle_root": "11" * 32,
                              "manifest_hash": "22" * 32, "total_chunks": 3})
        chain_journal.append({"type": "file", "file_id": "b", "merkle_root": "33" * 32,
                              "manifest_hash": "44" * 32, "total_chunks": 5})
        chain_journal.append({"type": "checkpoint", "ledger_head": "55" * 32, "seq": 10})

    def test_missing_journal_is_empty_not_an_error(self):
        self.assertEqual(chain_journal.read(), ([], None))

    def test_round_trip_and_chain_links(self):
        self.fill()
        recs, err = chain_journal.read()
        self.assertIsNone(err)
        self.assertEqual([r["type"] for r in recs], ["file", "file", "checkpoint"])
        self.assertEqual(recs[1]["prev"], recs[0]["hash"])

    def test_edited_line_detected_and_replay_stops_before_it(self):
        self.fill()
        p = chain_journal.journal_path()
        lines = p.read_text().splitlines()
        lines[1] = lines[1].replace("33" * 32, "ff" * 32)
        p.write_text("\n".join(lines) + "\n")
        recs, err = chain_journal.read()
        self.assertEqual(len(recs), 1)
        self.assertIn("line 2", err)

    def test_deleted_line_detected(self):
        self.fill()
        p = chain_journal.journal_path()
        lines = p.read_text().splitlines()
        p.write_text("\n".join([lines[0], lines[2]]) + "\n")
        self.assertIn("line 2", chain_journal.read()[1])

    def test_refuses_to_append_to_a_corrupted_journal(self):
        self.fill()
        p = chain_journal.journal_path()
        p.write_text(p.read_text().replace("11" * 32, "99" * 32))
        with self.assertRaises(RuntimeError):
            chain_journal.append({"type": "file", "file_id": "z"})

    def test_replay_restores_everything_into_an_empty_chain(self):
        self.fill()
        fake = FakeChain()
        stats = chain_journal.replay(fake)
        self.assertEqual((stats["files_replayed"], stats["checkpoints_replayed"]), (2, 1))
        self.assertEqual(fake.file_calls, ["a", "b"])

    def test_replay_is_idempotent(self):
        self.fill()
        fake = FakeChain()
        chain_journal.replay(fake)
        again = chain_journal.replay(fake)
        self.assertEqual((again["files_replayed"], again["files_skipped"]), (0, 2))
        self.assertEqual(again["checkpoints_skipped"], 1)

    def test_replay_skips_what_the_chain_already_has(self):
        self.fill()
        fake = FakeChain(anchored={"a"}, latest_seq=10)
        stats = chain_journal.replay(fake)
        self.assertEqual(fake.file_calls, ["b"])
        self.assertEqual(stats["checkpoints_skipped"], 1)

    def test_tampered_journal_replays_only_the_trusted_prefix(self):
        self.fill()
        p = chain_journal.journal_path()
        lines = p.read_text().splitlines()
        lines[1] = lines[1].replace("33" * 32, "ff" * 32)
        p.write_text("\n".join(lines) + "\n")
        fake = FakeChain()
        stats = chain_journal.replay(fake)
        self.assertEqual(fake.file_calls, ["a"])
        self.assertIsNotNone(stats["journal_error"])


if __name__ == "__main__":
    unittest.main()
