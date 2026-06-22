# dotfiles (GNU Stow)

One package, `home/`, which mirrors `$HOME` exactly. Stow symlinks its
contents into `~`.

## Install on a new machine (e.g. Void)

```sh
sudo xbps-install -S stow git        # Void
git clone <this-repo> ~/stow_dots
cd ~/stow_dots
stow -n -v home                      # DRY RUN: preview, check for conflicts
stow home                            # apply
```

If stow complains a file already exists in `~`, either delete that file
first, or use `stow --adopt home` (pulls the existing file into the repo,
then check `git diff`).

## Daily use

```sh
cd ~/stow_dots
stow home        # link
stow -D home     # unlink
stow -R home     # re-link after adding/removing files
```

To add a new config, drop it inside `home/` where it lives in your real
home dir, e.g. `home/.config/foo/` → links to `~/.config/foo/`.

## Notes
- SSH keys are intentionally **not** here (copy them by hand; don't symlink).
- `chadwm` is a build-it-yourself WM: `cd ~/.config/chadwm/chadwm && sudo make install`.
- `chadwm`/`eww` were upstream git repos, flattened in here. To track
  upstream again, re-add them as submodules.
