# Docker setup

Back to [SETUP.md](SETUP.md)

This is a rewrite of this [guide](https://www.cherryservers.com/blog/how-to-install-and-use-docker-compose-on-ubuntu-20-04) to install docker.

To begin, update your package list:
```bash
apt update -y
```

Next, you'll need these four packages to allow `apt` to work with HTTPS-based repositories:
- `ca-certificates` - A package that verifies SSL/TLS certificates.
- `curl` - A popular data transfer tool that supports multiple protocols including HTTPS.
- `gnupg` - An open source implementation of the Pretty Good Privacy (PGP) suite of cryptographic tools.
- `lsb-release` - A utility for reporting Linux Standard Base (LSB) versions.

Use this command to install those packages:
```bash
apt install ca-certificates curl gnupg lsb-release -y
```

Make a directory for Docker's GPG key:
```bash
mkdir /etc/apt/demokeyrings
```

Use `curl` to download Docker's keyring and pipe it into `gpg` to create a GPG file so `apt` trusts Docker's repo:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/demokeyrings/demodocker.gpg
```

Add the Docker repo to your system with this command:
```bash
 echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/demokeyrings/demodocker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
```

Now that you added Docker's repo, update your package lists again:
```bash
apt update -y
```

Next, install Docker-CE (Community Edition), the Docker-CE CLI, the containerd runtime, and Docker Compose with this command:
```bash
apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

You can verify Docker-CE, the Docker-CE CLI, containerd, and Docker Compose are installed by checking their versions with these commands:
```bash
docker --version; docker compose version;ctr version
```

It should look something like this:
```
Docker version 24.0.7, build afdd53b
Docker Compose version v2.21.0
Client:
  Version:  1.6.25
  Revision: d8f198a4ed8892c764191ef7b3b06d8a2eeb5c7f
  Go version: go1.20.10

Server:
  Version:  1.6.25
  Revision: d8f198a4ed8892c764191ef7b3b06d8a2eeb5c7f
  UUID: 234a5863-7cf4-4462-ac20-53b24bc001ef
```

Back to [SETUP.md](SETUP.md)