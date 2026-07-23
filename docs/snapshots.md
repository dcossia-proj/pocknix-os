# Snapshots, rollback and the update safety net

pocknix stays a fully **mutable** Arch system — `pacman -Syu` is still the update — but every
package transaction is wrapped in a btrfs snapshot, and rolling back is one QAM button (or one
command) plus a reboot. No bootloader menu is involved, so it works identically on the
sm8550 devices (ROCKNIX ABL, no menu at all) and the sm8250 devices (GRUB).

## How it works

**Root layout.** The root partition is btrfs with five subvolumes:

| Subvol | Mounted at | Rolls back? |
|---|---|---|
| `@` | `/` (as the filesystem **default**) | yes — the OS, including pacman's database |
| `@home` | `/home` | no — games, saves, settings survive |
| `@snapshots` | `/.snapshots` | no — the snapshots themselves |
| `@pacman-cache` | `/var/cache/pacman` | no — downloaded packages aren't duplicated per snapshot |
| `@var-log` | `/var/log` | no — logs survive for post-mortem |

Neither the kernel cmdline nor the fstab root line names a subvolume: the kernel mounts
whatever the filesystem's *default subvolume* is. That is the whole rollback mechanism —
`pocknix-rollback` points the default at a restored root and reboots. Zero boot-config
changes, one atomic btrfs operation as the commit point.

**Snapshots.** Two alpm hooks (package `pocknix-snapshots`) fire inside *every* pacman
transaction — the QAM updater, `pocknix-update`, or a plain `pacman -Syu` over ssh:

- `05-pocknix-snapshot` (PreTransaction): read-only snapshot of `/` into
  `/.snapshots/<id>/snapshot` + metadata in `info.json` (date, targets, whether a kernel
  was in the transaction). Skipped below 1 GiB free — **never blocks the update**.
- `99-pocknix-snapshot-post` (PostTransaction): marks the transaction committed, touches
  `/run/pocknix/reboot-required` when a kernel changed, prunes old snapshots.

Retention: newest **5** snapshots + **1** abandoned root, tunable in
`/etc/pocknix/snapshots.conf`.

**The kernel gap.** Boot files live on the FAT partition (`/flash`), outside btrfs. When the
rollback target's kernel differs from the running one, `pocknix-rollback` regenerates
`/flash/KERNEL` (and dtbs on arm-efi) **from the snapshot's own tree** (via the kernel
package deploy script in `SRCROOT`/staging mode), staged as `*.new` before the commit and
renamed after — so the kernel and its modules always match after the reboot. A crash inside
that tiny window is healed on the next boot by `pocknix-rollback-repair.service`.

## Using it

- **QAM:** Pocknix Control → Updater tab → *Roll Back Last Update* → Reboot.
- **CLI (desktop/ssh):**

```bash
pocknix-snapshots list          # what you can roll back to
pocknix-snapshots status        # running root / boots-next / free space
sudo pocknix-rollback           # newest snapshot, interactive confirm
sudo pocknix-rollback --to 0003 # a specific one
```

Rolling back a rollback works the same way — every rollback creates a fresh root from an
immutable read-only snapshot, and the abandoned root is kept (one deep) for inspection.

## Manual recovery (device won't boot after a kernel update)

Both kernel deploy paths keep the previous boot image as `/flash/KERNEL.bak`. If the device
no longer boots and you can't get a shell:

1. Power off. Put the SD in a card reader (internal installs: boot a pocknix SD instead and
   mount the internal FAT).
2. On the boot FAT partition:
   ```bash
   mv KERNEL KERNEL.bad
   mv KERNEL.bak KERNEL
   md5sum KERNEL > KERNEL.md5    # MANDATORY — the ABL refuses a KERNEL whose md5 mismatches
   ```
3. Boot. The old kernel now runs with the newer modules — degraded (Wi-Fi/audio may be
   missing) but alive. Run `sudo pocknix-rollback` on the device to make kernel and rootfs
   coherent again.

## Existing (ext4) installs

Images built before the btrfs switch stay ext4 and keep updating normally — the hooks and
the QAM rollback UI detect the filesystem and disable themselves. There is no in-place
migration: back up saves, reflash a current image, restore. New SD images and any internal
install made *from* a btrfs SD get the full snapshot layout.
