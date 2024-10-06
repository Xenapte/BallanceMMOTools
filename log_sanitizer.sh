#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 <logfile.log.gz>"
  exit 1
fi

input_file=$1
log_file="${input_file%.gz}"
# log files have the extension .log.gz
sanitized_log_file="${log_file%.log}_sanitized.log"

# Extract the log file
gzip -dk "$input_file"
mv $log_file $sanitized_log_file
sed -i -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/*.*.*.*/g' $sanitized_log_file
sed -i -E 's/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/********-****-****-****-************/g' $sanitized_log_file
gzip $sanitized_log_file

echo "Sanitized log saved to $sanitized_log_file.gz"
