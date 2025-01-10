from sys import argv, stderr, byteorder
from datetime import datetime
from collections import defaultdict

RECORD_HEADER = "BallanceMMO FlightRecorder\0"

def read_int(f, length=4):
  return int.from_bytes(f.read(length), byteorder=byteorder)

def main():
  if len(argv) != 2:
    print("Usage: python record_analyzer.py <filename>")
    return
  filename = argv[1]
  with open(filename, "rb") as f:
    header = f.read(len(RECORD_HEADER)).decode()
    if header != RECORD_HEADER:
      stderr.write("Invalid record file!\n")
      return
    print("=" * 80)
    print("BallanceMMO FlightRecorder Data")
    major_version = read_int(f, 1)
    minor_version = read_int(f, 1)
    subminor_version = read_int(f, 1)
    stage = read_int(f, 1)
    build = read_int(f, 1)
    print(f"Version: \t\t{major_version}.{minor_version}.{subminor_version}-{['alpha', 'beta', 'rc', ''][stage]}{build}")
    record_start_world_time = read_int(f, 8)
    print(f"Recorded at: \t\t{datetime.fromtimestamp(record_start_world_time).strftime('%Y-%m-%d %H:%M:%S')}")
    record_start_time = read_int(f, 8)

    type_names = []
    try:
      with open("message.hpp", "r") as msg_f:
        read_types = False
        for line in msg_f:
          line_strip = line.strip()
          if line_strip.startswith("enum opcode"):
            read_types = True
            types = ""
          if not read_types or line_strip.startswith("//"):
            continue
          if line_strip.startswith("};"):
            break
          types += line_strip
        type_names = types.split(",")
    except FileNotFoundError:
      print("*** Optional: place `message.hpp` under your PWD to see message type names ***")

    # [type, list[size]]
    record_data: dict[int, list[int]] = defaultdict(list[int])

    while True:
      record_time_bytes = f.read(8)
      if len(record_time_bytes) < 8:
        break # EOF
      record_time = int.from_bytes(record_time_bytes, byteorder=byteorder)
      record_length = read_int(f, 4)
      record_type = read_int(f, 4)
      record_data[record_type].append(record_length)
      f.seek(record_length - 4, 1) # type is part of the length

    duration = (record_time - record_start_time) # in microseconds
    print(f"Record length: \t\t{duration / 1e6 :.2f} seconds")
    print(f"Record end time: \t{datetime.fromtimestamp(record_start_world_time + duration / 1e6).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("Record data:")
    print("%-27s %-9s %-9s %-9s %-9s %-9s" % ("Type", "Count", "% Total", "Max", "Min", "Avg"))
    print("-" * 80)
    total_records = sum(len(record_lengths) for record_lengths in record_data.values())
    for record_type, record_lengths in sorted(record_data.items()):
      print("%-27s %-9d %-9.2f %-9d %-9d %-9.4g" % (type_names[record_type] if type_names else str(record_type), len(record_lengths), len(record_lengths) / total_records * 100, max(record_lengths), min(record_lengths), sum(record_lengths) / len(record_lengths)))
    print("-" * 80)
    print("%-27s %-9d %-9.2f %-9s %-9s %-9.4g" % ("(Total)", total_records, 100, "-", "-", sum(sum(record_lengths) for record_lengths in record_data.values()) / total_records))
    print("=" * 80)
    

if __name__ == "__main__":
  main()
