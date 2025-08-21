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

args = parser.parse_args()

moving = not args.no_move
mockclient_command = args.mockclient_command if args.mockclient_command else ["./BallanceMMOMockClient"]
print(f"Using mockclient command: {mockclient_command}")


def exit_handler():
    global moving
    print("Interrupted by user, exiting...")
    moving = False
    for i in range(args.count):
        subprocess.run(["screen", "-S", args.screen_name, "-p", str(i), "-X", "stuff", "^Mstop^M"])
        time.sleep(0.2) # hardcoded delay to allow mock client to stop properly
    subprocess.run(["screen", "-S", args.screen_name, "-X", "quit"])
    exit(0)

def move_indefinitely():
    while moving:
        subprocess.run(["screen", "-S", args.screen_name, "-X", "at", "#", "stuff", "translate^M"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(args.movement_interval)


name_len = int(math.log10(args.count)) + 1 if args.count > 1 else 1

try:
    for i in range(args.count):
        if i == 0:
            subprocess.run(["screen", "-dmS", args.screen_name] + mockclient_command + ["-n", f"{args.name}{i+1 :0{name_len}d}"])
        else:
            subprocess.run(["screen", "-S", args.screen_name, "-X", "screen"] + mockclient_command + ["-n", f"{args.name}{i+1 :0{name_len}d}"])
        time.sleep(args.spawn_interval)

    print(f"Spawned {args.count} mock clients with prefix '{args.name}' and screen name '{args.screen_name}'.")
    print(f"To interact with the mock clients directly, use the command: `screen -r {args.screen_name}`.")
    print(f"To dispatch more complex commands to the mock clients, type in the console or use the command: `screen -S {args.screen_name} -X at # stuff 'your_command^M'`.")
    print(f"Alternatively, if you want to keep the order, use `for i in {{0..{args.count-1}}}; do screen -S {args.screen_name} -p $i -X stuff 'your_command^M'; done`.")

    import readline

    def rprint(*args, **kwargs):
        print("\r", end="")
        print(*args, **kwargs)
        readline.redisplay()
        # readline.add_history(" ".join(map(str, args)))

    if moving:
        threading.Thread(target=move_indefinitely, daemon=True).start()

    ordered = True

    while True:
        try:
            input_str = input(f"{args.screen_name}> ").strip()
            cmd_args = input_str.split(" ")
            if not cmd_args:
                continue
            cmd = cmd_args[0].strip().lower()
            if cmd in ["exit", "quit", "stop"]:
                exit_handler()
            if cmd == "order":
                ordered = not ordered
                if ordered:
                    rprint("Mock clients will now execute commands in order.")
                else:
                    rprint("Mock clients will now execute commands in parallel.")
            elif cmd == "move":
                moving = not moving
                if moving:
                    rprint("Mock clients will now move.")
                    threading.Thread(target=move_indefinitely, daemon=True).start()
                else:
                    rprint("Mock clients will stop moving.")
            else:
                if ordered:
                    for i in range(args.count):
                        subprocess.run(["screen", "-S", args.screen_name, "-p", str(i), "-X", "stuff", f"{input_str}^M"])
                else:
                    subprocess.run(["screen", "-S", args.screen_name, "-X", "at", "#", "stuff", f"{input_str}^M"])

        except EOFError:
            break

    exit_handler()

except KeyboardInterrupt:
    exit_handler()