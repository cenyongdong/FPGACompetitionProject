"""Exercise real Windows IPC with a dummy credential and no network access."""
import argparse
import json
from multiprocessing.connection import Client
from pathlib import Path
import subprocess
import sys
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    arguments = parser.parse_args()
    if arguments.worker:
        import router_transport as transport
        transport.getpass.getpass = lambda _: 'local-test-only'

        def simulated_ssh(directory, user, password, script, data, timeout):
            assert password == b'local-test-only'
            return 0, b'LOCAL_IPC_OK\n', b''

        transport.ssh_run = simulated_ssh
        transport.serve(argparse.Namespace(directory=str(arguments.worker), user='admin'))
        return
    project = Path(__file__).resolve().parents[3]
    directory = project / '.local' / ('nexmon-ipc-check-' + uuid.uuid4().hex)
    directory.mkdir()
    (directory / 'known_hosts').write_text('LOCAL TEST ONLY; never used by SSH\n')
    process = subprocess.Popen([sys.executable, '-u', __file__, '--worker', str(directory)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 8
        while not (directory / 'connection.json').exists():
            if process.poll() is not None or time.monotonic() > deadline:
                raise AssertionError('Local IPC worker did not become ready')
            time.sleep(0.05)
        info = json.loads((directory / 'connection.json').read_text())
        # A probe that connects then closes must not discard the owner's credential.
        with Client(info['pipe'], family='AF_PIPE'):
            pass
        time.sleep(0.15)
        assert process.poll() is None, 'An empty local connection terminated the worker'
        with Client(info['pipe'], family='AF_PIPE') as connection:
            connection.send(dict(operation='exec', script='local simulation only', timeout=5))
            response = connection.recv()
        assert response['exit_code'] == 0 and response['stdout'] == 'LOCAL_IPC_OK\n'
        with Client(info['pipe'], family='AF_PIPE') as connection:
            connection.send(dict(operation='stop'))
            assert connection.recv()['stopped']
        output, errors = process.communicate(timeout=5)
        assert process.returncode == 0, errors.decode(errors='replace')
        result = dict(passed=True, network_connections=0, device_commands=0,
                      empty_connection_survived=True, simulated_command_passed=True,
                      stopped_cleanly=True)
        print(json.dumps(result))
    finally:
        if process.poll() is None:
            process.terminate()
        output, errors = process.communicate(timeout=5)
        (directory / 'worker.stdout').write_bytes(output)
        (directory / 'worker.stderr').write_bytes(errors)
        print('LOCAL_TEST_DIRECTORY=' + str(directory))


if __name__ == '__main__':
    main()
