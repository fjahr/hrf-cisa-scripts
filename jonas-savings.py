# Transaction with segwit v1 spends and outputs.
# Outputs size in bytes and weight units.
def tx_size(n_inputs, n_outputs):
    assert(n_inputs <= 252 and n_outputs <= 252)
    return list(map(lambda mult: (
        mult*(
            4     # version
            + 1   # number of inputs
            + n_inputs * (
                32 + 4 # prevout
                + 1    # script len
                + 4)   # sequence
            + 1   # number of outputs
            + n_outputs * (
                8       # amount
                + 1     # script len
                + 34)   # script
             + 4)  # locktime
         + 2 # witness flag & marker
         + n_inputs * (
             1       # witness stack items
             + 1     # witness item len
             + 64)), # BIP-340 sig
      [1, 4]))


# Average according to https://transactionfee.info/
n_inputs = 2.12
n_outputs = 2.64

size = tx_size(n_inputs, n_outputs)
half_agged = map(lambda s: s - n_inputs*32, size)
full_agged = map(lambda s: s - (n_inputs-1)*64, size)
both_agged = map(lambda s: s - (n_inputs-1)*64 - 32, size)
max_agged = map(lambda s: s - n_inputs*64, size)

def savings(name, agged_sizes):
    return [name] + ["%.1f%%" % ((1 - a/b)*100) for (a,b) in zip(agged_sizes, size)]

print([
    [ "", "bytes", "weight units" ],
    None,
    savings("half aggregation", half_agged),
    savings("full aggregation", full_agged),
    savings("both", both_agged),
    savings("max (like infinite large full agged coinjoin)", max_agged)
])
