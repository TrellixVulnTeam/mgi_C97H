import click, glob, json, os, shutil, tempfile, unittest, yaml
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import MagicMock, patch

from cw.conf import CromwellConf

class CwOutputsCmdTest(unittest.TestCase):
    def setUp(self):
        self.temp_d = tempfile.TemporaryDirectory()
        self.tasks_and_outputs = { "test.task1": ["file1"], "test.task2": ["file2", "file3"], "test.missing_task": ["?"]}
        self.tasks_and_outputs_fn = os.path.join(self.temp_d.name, "mypipe_tno.yaml")
        with open(self.tasks_and_outputs_fn, "w") as f:
            f.write(yaml.dump(self.tasks_and_outputs))

    def tearDown(self):
        self.temp_d.cleanup()

    def test_resolve_tasks_and_outputs(self):
        from cw.outputs_cmd import resolve_tasks_and_outputs as fun

        # file
        got = fun(self.tasks_and_outputs_fn)
        self.assertDictEqual(got, self.tasks_and_outputs)

        # encode hic
        got = fun("encode_hic")
        self.assertTrue(type(got), dict)

        # error
        with self.assertRaisesRegex(Exception, f"No such known pipeline <unknown>."):
            fun("unknown")

    def test_collect_shards_outputs(self):
        from cw.outputs_cmd import collect_shards_outputs as fun

        task_name = "test.task2"
        task = [
            {
                "shardIndex": 0,
                "executionStatus": "Done",
                "outputs": {
                    "file2": "file2",
                    "file3": "file3",
                },
            },
            {
                "shardIndex": 0,
                "executionStatus": "Failed",
                "outputs": {
                    "file2": "file2",
                    "file3": "file3",
                },
            },
            {
                "shardIndex": 1,
                "executionStatus": "Done",
                "outputs": {
                    "file2": "file2",
                    "file3": "file3",
                },
            },
            {
                "shardIndex": 2,
                "executionStatus": "Failed",
                "outputs": {
                    "file2": "file2",
                    "file3": "file3",
                },
            },
        ]
        shards, shard_idxs = fun(task, self.tasks_and_outputs[task_name])
        self.assertEqual(shards, [[0, ["file2", "file3"]], [1, ["file2", "file3"]]])
        self.assertEqual(shard_idxs, set([0, 1, 2]))

    @patch("cw.server_cmd.start_server")
    def test_outputs_cmd(self, p):
        from cw.outputs_cmd import outputs_cmd as cmd
        runner = CliRunner()

        # create files
        # create metadata
        task1_shard0_dn = os.path.join(self.temp_d.name, "runs", "test", "UUID", "call-task1")
        task1_shard1_dn = os.path.join(self.temp_d.name, "runs", "test", "UUID", "call-task1")
        task2_dn = os.path.join(self.temp_d.name, "runs", "test", "UUID", "call-task2")
        for dn in task1_shard0_dn, task1_shard1_dn, task2_dn:
            os.makedirs(dn, exist_ok=True)
        task1_file1_1 = os.path.join(task1_shard0_dn, "file1-1")
        task1_file1_2 = os.path.join(task1_shard1_dn, "file1-2")
        task2_file2 = os.path.join(task2_dn, "file2")
        task2_file3 = os.path.join(task2_dn, "file3")
        for fn in task1_file1_1, task1_file1_2, task2_file2, task2_file3:
            Path(fn).touch()
        metadata = {
            "workflowName": "test",
            "calls": {
                "test.task1": [
                    {
                        "shardIndex": 0,
                        "executionStatus": "Done",
                        "outputs": {
                            "file1": task1_file1_1,
                            "nocopy": "nocopy",
                        },
                    },
                    {
                        "shardIndex": 0,
                        "executionStatus": "Failed",
                        "outputs": {
                            "file1": "failed",
                            "nocopy": "nocopy",
                        },
                    },
                    {
                        "shardIndex": 1,
                        "executionStatus": "Done",
                        "outputs": {
                            "file1": task1_file1_2,
                            "nocopy": "failed",
                        },
                    },
                ],
                "test.task2": [
                    {
                        "shardIndex": 0,
                        "executionStatus": "Done",
                        "outputs": {
                            "file2": task2_file2,
                            "file3": task2_file3,
                            "nocopy": "nocopy",
                        },
                    },
                    {
                        "shardIndex": 0,
                        "executionStatus": "Failed",
                        "outputs": {
                            "file2": "failed",
                            "file3": "failed",
                            "nocopy": "nocopy",
                        },
                    },
                ],
                "test.task3": [ # ignored
                    {
                        "shardIndex": 0,
                        "executionStatus": "Done",
                        "outputs": {
                            "file": "ignored",
                        },
                    },
                ],
            }
        }
        metadata_fn = os.path.join(self.temp_d.name, "metadata.json")
        with open(metadata_fn, "w") as f:
            json.dump(metadata, f)
        dest_dn = os.path.join(self.temp_d.name, "outputs")
        os.makedirs(dest_dn, exist_ok=True)

        result = runner.invoke(cmd, [metadata_fn, dest_dn, self.tasks_and_outputs_fn], catch_exceptions=False)
        try:
            self.assertEqual(result.exit_code, 0)
        except:
            print(result.output)
            raise
        expected = f"""[INFO] Task <test.missing_task> files: <?>
[WARN] No task found for <test.missing_task> ... skipping
[INFO] Task <test.task1> files: <file1>
[INFO] Found 2 of 2 tasks DONE
[INFO] Copy {task1_file1_1} to {self.temp_d.name}/outputs/task1/shard0
[INFO] Copy {task1_file1_2} to {self.temp_d.name}/outputs/task1/shard1
[INFO] Task <test.task2> files: <file2 file3>
[INFO] Found 1 of 1 tasks DONE
[INFO] Copy {self.temp_d.name}/runs/test/UUID/call-task2/file2 to {self.temp_d.name}/outputs/task2
[INFO] Copy {self.temp_d.name}/runs/test/UUID/call-task2/file3 to {self.temp_d.name}/outputs/task2
[INFO] Done
"""
        self.maxDiff = 10000
        self.assertEqual(result.output, expected)

        got = []
        for (root, dirs, files) in os.walk(dest_dn):
            for fn in files:
                got.append(os.path.join(root, fn))
        expected = ["task1/shard0/file1-1", "task1/shard1/file1-2", "task2/file2", "task2/file3"]
        expected = list(map(lambda f: os.path.join(dest_dn, f), expected))
        self.assertEqual(got.sort(), expected.sort())

if __name__ == '__main__':
    unittest.main(verbosity=2)
