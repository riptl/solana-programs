# solana-programs

All [Solana](https://solana.com/) mainnet programs as of 2022-02-11.

### Why?

Security research.

### What?

ELF files, as they appear on-chain.

## Usage

### Installation

```shell
python3 -m venv ./env
source ./env/bin/activate
pip install -r requirements.txt
```

### Dumping programs

```
% python -m solbpf_analyze dump testnet

solana-core 1.9.6 (feat: 2191737503)

Dumping to /Users/richard/prj/solana-programs/programs/testnet

Listing BPF Loader Legacy
Got 8311 BPF Loader Legacy accounts
Listing BPF Loader
Got 1483 BPF Loader accounts
Listing BPF Loader (upgradeable)
Got 3887 BPF Loader Upgradeable accounts

Starting dump
 10%|████████▊                                                                                    | 1300/13681 [00:12<01:50, 111.61it/s]
```
