set -eu
mkdir -p /tmp/source /tmp/result
cd /tmp/source
tar -xzf /tmp/source.tar.gz
gcc -std=c99 -O2 -march=armv8-a -fno-fast-math -ffp-contract=off -Wall -Wextra -Wno-unused-parameter -Werror campaign/arithmetic_controls.c -o /tmp/result/controls
gcc -std=c99 -O2 -march=armv8-a -fno-fast-math -ffp-contract=off -Wall -Wextra -Wno-unused-parameter -Werror campaign/cross_runner.c generated/zero_reset.c generated/tracking_reset.c -o /tmp/result/runner
/tmp/result/controls > /tmp/result/controls-native.json
qemu-aarch64 -cpu cortex-a53 -L / /tmp/result/controls > /tmp/result/controls-qemu.json
/tmp/result/runner < /tmp/inputs.txt > /tmp/result/native.txt
qemu-aarch64 -cpu cortex-a53 -L / /tmp/result/runner < /tmp/inputs.txt > /tmp/result/qemu.txt
readelf -h -l /tmp/result/runner > /tmp/result/elf.txt
sha256sum /usr/bin/gcc /usr/bin/qemu-aarch64 /lib/ld-musl-aarch64.so.1 /tmp/result/controls /tmp/result/runner > /tmp/result/binary-hashes.txt
sha256sum campaign/*.c generated/* /tmp/inputs.txt > /tmp/result/input-hashes.txt
gcc -Q --help=optimizers -O2 -fno-fast-math -ffp-contract=off > /tmp/result/optimizer-settings.txt
