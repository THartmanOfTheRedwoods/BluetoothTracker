import shelve
import subprocess
import re
import asyncio
from time import strftime, gmtime

KNOWN_DEVICES = {
    'ac:c0:48:67:a2:cc': 'Viable',
    '08:a5:df:5a:b7:96': 'Sivert was here',
    '20:15:82:83:d6:8d': 'Ethan'
}

# Simulate async input using a thread-based fallback
async def async_input(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)

# Monitor user input concurrently
async def handle_user_input():
    while True:
        user_cmd = await async_input("Pres Enter (or 'exit'): ")

        with shelve.open("device_log") as db:
            for key, data in db.items():
                print(f"{key}: {data}")

        if user_cmd.strip().lower() == "exit":
            print("Exiting input loop...")
            break

def match_line(line):
    pattern =r"^(?:[0-9A-Fa-f]{2}([-:]))(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}"
    found = re.match(pattern, line)
    if found is not None:
        return line

def ds_line(line):
    if line:
        return re.split(r' +', line.strip(), maxsplit=3)

def add_device(device):
    key = device[0]
    if key in KNOWN_DEVICES:
        # devices.setdefault(key, []).append((strftime( "%Y-%m-%d %H:%M:%S", gmtime()), device[-1]))
        with shelve.open("device_log") as db:
            data = (strftime("%Y-%m-%d %H:%M:%S", gmtime()), device[-1])
            if key in db:
                time_list = db[key]
                time_list.append(data)
                db[key] = time_list
            else:
                db[key] = [data]
        print("Logged devices in the shelf database.")

async def run_command(command, *args):
    process = await asyncio.create_subprocess_exec(
        command, *args,  # or your command
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    # print(stdout)
    return stdout.decode()

async def scan():
    command = r".\execs\BluetoothCL.exe -timeout 5"
    while True:
        print("Scanning...")
        try:
            output = await run_command('powershell', '-Command', command)
            for line in output.split('\n'):
                if len(line) > 0:
                    clean_line = ds_line(match_line(line))
                    if clean_line:
                        add_device(clean_line)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            print(f"Stderr: {e.stderr}")

async def main():
    scanner_task = asyncio.create_task(scan())
    input_task = asyncio.create_task(handle_user_input())

    await asyncio.wait(
        [scanner_task, input_task],
        return_when=asyncio.FIRST_COMPLETED  # Stop if input exits
    )

    # Optionally cancel the other task if still running
    if not scanner_task.done():
        scanner_task.cancel()
        print("Scanner task cancelled.")


if __name__ == '__main__':
    asyncio.run(main())
