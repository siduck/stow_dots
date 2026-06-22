# system/ — root-owned files (NOT stowed)

These are `/etc` configs. They are **copies for backup**, not stow symlinks.
Symlinking root config into a user-owned repo is a privilege-escalation risk
(`doas`/`sudo` require their config to be root-owned and not user-writable),
so install them by copying, as root.

## Install on a new machine (Void)

```sh
doas cp system/etc/doas.conf      /etc/doas.conf
doas chown root:root /etc/doas.conf && doas chmod 0644 /etc/doas.conf

doas mkdir -p /etc/iwd
doas cp system/etc/iwd/main.conf  /etc/iwd/main.conf
```

Packages: `doas`, `iwd`, and `resolvconf` (referenced by iwd's
`NameResolvingService`). Enable iwd: `doas ln -s /etc/sv/iwd /var/service/`.

## Wifi passwords are NOT here
Saved networks (with PSKs) live in `/var/lib/iwd/` (root-only). To carry them:

```sh
doas cp -a /var/lib/iwd /somewhere/safe   # on the OLD machine
# then restore to /var/lib/iwd on the new one (root:root, 0600 files)
```
Treat these as secrets — do not commit them to a public repo.
