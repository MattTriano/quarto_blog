# Installs

## Update and Upgrade

Update
```bash
sudo apt update
```

Optionally look at any upgradable packages
```bash
apt list --upgradable
```

and then, if you want to upgrade those packages

```bash
sudo apt upgrade
```

## vim

```bash
sudo apt install vim
```

## SSH

```bash
sudo apt install openssh-server
```

### Harden SSH

Open up the sshd_config file
```bash
sudo vim /etc/ssh/sshd_config
```

and scan through the file for these config options, uncomment them, and change their values to match the ones below.

```txt
PermitRootLogin no
...
PasswordAuthentication no
PermitEmptyPasswords no
...
ClientAliveInterval 1800
ClientAliveCountMax 2
```

and exit out. There's plenty more you can do, but this is a good bare minimum.

### Monitoring SSH logins

SSH login attempts are logged by the SSH daemon and you can view them via
```bash
cat /var/log/auth.log | grep sshd
```

To see all currently logged in users, use

```bash
who
```

or

```bash
w
```

And to see every recent login,

```bash
last
```


## Docker

1. Set up the [Docker Apt repo](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)

Add Docker's official GPG key:
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

then add the repository to Apt sources and retrieve pkg metadata from that repo
```bash
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

2. Install Docker packages

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

3. Configure docker to run in [rootless mode](https://docs.docker.com/engine/security/rootless/)
This is an experiment for me, as all of my prior docker experience is with docker running as root.

3.1. [Prereqs](https://docs.docker.com/engine/security/rootless/#prerequisites)

3.1.1. Install uidmap

```bash
sudo apt install uidmap dbus-user-session
```

If `dbus-user-session` wasn't already installed, log out and log back in. You can do this via a hard reboot with the command

```bash
sudo shutdown -r now
```

3.2. Run the `dockerd-rootless-setuptool.sh` script's `install` command

```bash
dockerd-rootless-setuptool.sh install
```

This will finish quickly and the console output will include several instructions.

3.3. Follow the instructions from the console output

To allow the docker-daemon to run when the user is logged out (but still as the user, not as `root`)

```bash
sudo loginctl enable-linger $(whoami)
```

To start the docker-daemon on startup

```bash
systemctl --user enable docker
```

And add these environment variable declarations to your `~/.bashrc` file.

```bash
...
export PATH=/usr/bin:$PATH

[INFO] Some applications may require the following environment variable too:
export DOCKER_HOST=unix:///run/user/1000/docker.sock
```

4. Check that docker runs

```bash
docker container run --rm hello-world
```

## Tailscale

1. [Install tailscale](https://tailscale.com/kb/1017/install/) onto each machine you want to add to the network.

2. Start up ssh via tailscale on the destination server machine with `tailscale up --ssh`
2.a. Adjust [ACLs](https://tailscale.com/kb/1018/acls/#acl-rules/) to limit access

3. Connect to the server from a remote machine
3.a. On the remote machine looking to connect to the server, look up the name of the server

```bash
tailscale status
```

3.b. `ssh` to the server

```bash
tailscale ssh {server_name}
```

3.c. Authenticate via whatever means you used when setting up your tailscale user account.




