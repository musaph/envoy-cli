# envoy-cli

A CLI tool for managing and syncing .env files across environments using encrypted remote stores.

## Installation

```bash
pip install envoy-cli
```

Or install from source:

```bash
git clone https://github.com/yourusername/envoy-cli.git
cd envoy-cli
pip install -e .
```

## Usage

Initialize a new envoy project:

```bash
envoy init
```

Push your local .env file to the remote store:

```bash
envoy push production
```

Pull environment variables from the remote store:

```bash
envoy pull production
```

List all available environments:

```bash
envoy list
```

Sync variables across multiple environments:

```bash
envoy sync staging production
```

## Features

- 🔐 End-to-end encryption for sensitive environment variables
- 🔄 Sync .env files across multiple environments
- ☁️ Support for multiple remote stores (AWS S3, Google Cloud Storage, Azure Blob)
- 🔑 Secret key management with automatic rotation
- 📝 Version control for environment configurations
- 🚀 Simple and intuitive CLI interface

## License

MIT