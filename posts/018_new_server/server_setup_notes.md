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



## Docker

1. Set up the [Docker Apt repo](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)



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
ssh {server_name}
```

3.c. Authenticate via whatever means you used when setting up your tailscale user account.



