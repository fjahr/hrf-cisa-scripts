#!/usr/bin/env python3

import sys
import subprocess
import json
import os


bitcoin_cli = os.environ.get('CLI')

def run_cli_command(command_args):
    """
    Run a bitcoin-cli command with the given arguments.
    Returns the stdout output as a string if successful,
    or exits with an error if the command fails.
    """
    result = subprocess.run(command_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command_args)}\n{result.stderr}")
        sys.exit(1)

    return result.stdout.strip()

def count_signatures_in_tx(tx):
    """
    Naive heuristic to count the number of signatures in a transaction
    by examining scriptSig.asm and txinwitness fields.
    """
    total_sigs = 0

    for vin in tx.get("vin", []):
        script_sig_asm = vin.get("scriptSig", {}).get("asm", "")
        for chunk in script_sig_asm.split():
            if chunk.startswith("304"):
                total_sigs += 1

        witness_data = vin.get("txinwitness", [])
        for wd in witness_data:
            if wd.startswith("304"):
                total_sigs += 1

    return total_sigs

def main(start_block, end_block):
    total_blocks = 0
    total_transactions = 0
    total_inputs = 0
    total_outputs = 0
    total_signatures = 0

    for height in range(start_block, end_block + 1):
        block_hash = run_cli_command([bitcoin_cli, "getblockhash", str(height)])

        block_data_raw = run_cli_command([bitcoin_cli, "getblock", block_hash, "2"])
        block_data = json.loads(block_data_raw)

        transactions = block_data.get("tx", [])

        total_blocks += 1
        total_transactions += len(transactions)

        for tx in transactions:
            vin = tx.get("vin", [])
            vout = tx.get("vout", [])
            total_inputs += len(vin)
            total_outputs += len(vout)

            sig_count = count_signatures_in_tx(tx)
            total_signatures += sig_count

        if height % 1000 == 0:
            print(f"Scanned block {height}")

    if total_blocks == 0:
        print("No blocks found in the given range.")
        return

    if total_transactions == 0:
        print("No transactions found in the given range.")
        return

    avg_tx_per_block = total_transactions / total_blocks
    avg_inputs_per_tx = total_inputs / total_transactions
    avg_outputs_per_tx = total_outputs / total_transactions
    avg_signatures_per_block = total_signatures / total_blocks
    avg_signatures_per_tx = total_signatures / total_transactions

    print(f"Results for blocks {start_block} through {end_block}:")
    print(f"  Average transactions per block: {avg_tx_per_block:.2f}")
    print(f"  Average inputs per transaction: {avg_inputs_per_tx:.2f}")
    print(f"  Average outputs per transaction: {avg_outputs_per_tx:.2f}")
    print(f"  TOTAL signatures in the entire range: {total_signatures}")
    print(f"  Average signatures per block: {avg_signatures_per_block:.2f}")
    print(f"  Average signatures per transaction: {avg_signatures_per_tx:.2f}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <start_block> <end_block>")
        sys.exit(1)

    start_height = int(sys.argv[1])
    end_height = int(sys.argv[2])

    main(start_height, end_height)
