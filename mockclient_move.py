import subprocess
import argparse
import time
import math
import threading

if __name__ != "__main__":
    raise ImportError("This script is not meant to be imported as a module.")

parser = argparse.ArgumentParser(description="spawns multiple mock clients. can be used for trolling.")

parser.add_argument("mockclient_command", nargs=argparse.REMAINDER, help="command of mockclient executables, minus name settings; default: `./BallanceMMOMockClient`.")
parser.add_argument("-c", "--count", type=int, required=True, help="number of mock clients to spawn; required argument.")
parser.add_argument("-n", "--name", type=str, default="f", help="prefix of the mock clients; default: `f` (so f1, f2, ...).")
parser.add_argument("--spawn-interval", type=float, default=0.2, help="time interval between each mock client spawn in seconds; default: 0.2 seconds.")
parser.add_argument("-i", "--movement-interval", type=float, default=0.2, help="time interval between mock client interactions in seconds; default: 0.2 seconds.")
# parser.add_argument("-p", "--pattern", type=str, default="bmmo-#-mock", help="prefix for the GNU Screen names; default: `bmmo-#-mock`. use `#` to denote the mock client number. an infix like in the default is recommended as GNU Screen normally does a fuzzy match on the name, and refuses to execute if there are multiple matches.")
parser.add_argument("-s", "--screen-name", type=str, default="bmmo-mock", help="prefix for the GNUScreen names; default: `bmmo-mock`.")
parser.add_argument("--no-move", help="if set, mock clients will not move. Default: False.", action="store_true")

sys_args = parser.parse_args()

moving = not sys_args.no_move
mockclient_command = sys_args.mockclient_command if sys_args.mockclient_command else ["./BallanceMMOMockClient"]
print(f"Using mockclient command: {mockclient_command}")

print("Note that this script assumes that you have GNU Screen installed and configured properly (e.g. no skipping of the #0 window), and that the mock client command is executable. If you encounter issues, please check your GNU Screen installation and the mock client command.")
print("-" * 40)


def exit_handler(*args):
    global moving
    print("\nInterrupted by user, exiting...")
    moving = False
    for i in range(sys_args.count):
        subprocess.run(["screen", "-S", sys_args.screen_name, "-p", str(i), "-X", "stuff", "^Mstop^M"])
        time.sleep(0.2) # hardcoded delay to allow mock client to stop properly
    subprocess.run(["screen", "-S", sys_args.screen_name, "-X", "quit"])
    exit(0)

def move_indefinitely():
    while moving:
        subprocess.run(["screen", "-S", sys_args.screen_name, "-X", "at", "#", "stuff", "translate^M"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(sys_args.movement_interval)


name_len = int(math.log10(sys_args.count)) + 1 if sys_args.count > 1 else 1

try:
    def spawn_noninitial_mock_client(index):
        subprocess.run(["screen", "-S", sys_args.screen_name, "-X", "screen", str(index - 1)] + mockclient_command + ["-n", f"{sys_args.name}{index :0{name_len}d}"])

    for i in range(sys_args.count):
        if i == 0:
            subprocess.run(["screen", "-dmS", sys_args.screen_name] + mockclient_command + ["-n", f"{sys_args.name}{i+1 :0{name_len}d}"])
        else:
            spawn_noninitial_mock_client(i + 1)
        time.sleep(sys_args.spawn_interval)

    print(f"Spawned {sys_args.count} mock clients with prefix '{sys_args.name}' and screen name '{sys_args.screen_name}'.")
    print(f"To interact with the mock clients directly, use the command: `screen -r {sys_args.screen_name}`.")
    print(f"To dispatch more complex commands to the mock clients, type in the console or use the command: `screen -S {sys_args.screen_name} -X at # stuff \"cmd^M\"`.")
    print(f"Alternatively, if you want to keep the order, use `for i in {{0..{sys_args.count-1}}}; do screen -S {sys_args.screen_name} -p $i -X stuff \"cmd^M\"; done`.")
    print("-" * 40)
    print("Type `help` for available commands. Type `exit` or press Ctrl+D to quit.")

    import readline

    def rprint(*args, **kwargs):
        print("\r", end="")
        print(*args, **kwargs)
        readline.redisplay()
        # readline.add_history(" ".join(map(str, args)))

    if moving:
        threading.Thread(target=move_indefinitely, daemon=True).start()

    ordered = True

    available_commands = {}
    def add_command(names: list[str], func):
        global available_commands
        for name in names:
            available_commands[name] = func

    def completer(text, state):
        options = [cmd for cmd in available_commands if cmd.startswith(text)]
        return options[state] if state < len(options) else None

    readline.set_completer(completer)
    readline.set_completer_delims(' \t')
    readline.parse_and_bind('tab: complete')

    add_command(["help"], lambda *args: rprint("Available commands:", ", ".join(sorted(available_commands.keys())),
                                               "\nOther unmatched commands will be sent to all mock clients."))

    add_command(["exit", "quit", "stop"], exit_handler)
    def toggleorder(*args):
        global ordered
        ordered = not ordered
        rprint("Mock clients will now execute commands " + ("in order." if ordered else "in parallel."))
    add_command(["toggleorder"], toggleorder)
    def togglemove(*args):
        global moving
        moving = not moving
        if moving:
            rprint("Mock clients will now move.")
            threading.Thread(target=move_indefinitely, daemon=True).start()
        else:
            rprint("Mock clients will stop moving.")
    add_command(["togglemove"], togglemove)
    def respawn(*args):
        if len(args) < 2:
            rprint("Usage: respawn <mock_client_number>")
            return
        try:
            index = int(args[1])
            if index < 0 or index > sys_args.count:
                rprint(f"Invalid mock client number: {index}. Must be between 1 and {sys_args.count}.")
                return
            rprint(f"Respawning mock client #{index}...")
            if subprocess.run(["screen", "-S", sys_args.screen_name, "-p", str(index - 1), "-Q", "title"]).returncode == 0: # still running
                rprint(f"Mock client #{index} is still running. Stopping it first...")
                subprocess.run(["screen", "-S", sys_args.screen_name, "-p", str(index - 1), "-X", "stuff", "^Mstop^M"])
                time.sleep(0.5)
            spawn_noninitial_mock_client(index)
        except ValueError:
            rprint("Invalid mock client number. Must be an integer.")
    add_command(["respawn"], respawn)

    while True:
        try:
            input_str = input(f"\r{sys_args.screen_name}> ").strip()
            cmd_args = input_str.split(" ")
            if not cmd_args:
                continue
            cmd = cmd_args[0].strip().lower()
            if cmd in available_commands:
                available_commands[cmd](*cmd_args)
            else:
                if ordered:
                    for i in range(sys_args.count):
                        if subprocess.run(["screen", "-S", sys_args.screen_name, "-p", str(i), "-X", "stuff", f"{input_str}^M"]).returncode != 0:
                            rprint(f"Error executing command on mock client #{i + 1}. Trying to respawn...")
                            spawn_noninitial_mock_client(i + 1)
                else:
                    subprocess.run(["screen", "-S", sys_args.screen_name, "-X", "at", "#", "stuff", f"{input_str}^M"])

        except EOFError:
            break

    exit_handler()

except KeyboardInterrupt:
    exit_handler()