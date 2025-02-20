#!/usr/bin/env python3
from sys import argv

BYTES_TX=10                  # version: 4 bytes, n_inputs: 1 byte, n_outputs: 1 byte, locktime: 4 bytes
BYTES_WITNESS=2              # witness marker/flag: 2 bytes
BYTES_PER_INPUT=41           # prevout: 36 bytes, scriptlen: 1 byte, sequence: 4 bytes
BYTES_PER_OUTPUT=43          # amount: 8 bytes, scriptlen: 1 byte, script: 34 bytes
BYTES_PER_WITNESS_STACK=66   # stacklen: 1 byte, itemlen: 1 byte, bip40 sig: 64 bytes
VBYTES_SHARED=(BYTES_TX * 4 + BYTES_WITNESS) / 4  # fixed amount of vbytes, regardless of the number of participants
SATS_PER_VBYTE=10


def calculate_savings(n_inputs, n_outputs, n_participants):
    tx_vbytes = (
        (
            BYTES_TX
            + BYTES_PER_INPUT*n_inputs
            + BYTES_PER_OUTPUT*n_outputs
        )*4             # non-witness data, multiplied by 4
        + BYTES_WITNESS # witness data
        + BYTES_PER_WITNESS_STACK*n_inputs
    ) / 4               # divide weight units by 4 for vbytes

    # In this scenario, the single participant pays for the entire transaction
    without_cisa_alone = tx_vbytes*SATS_PER_VBYTE
    print(tx_vbytes)

    # In a collaborative transaction, such as a coinjoin, each participant pays
    # for their own inputs and outputs and then splits the cost of the "shared bytes"
    # of the transaction. So there is always an incentive to create a transaction
    # with other participants, to "split the bill" on the shared bytes of the transaction.
    # The problem today is coordinating multiparties to create the transaction is not
    # trivial, and the savings opportunity is quite low: for any transaction, the shared
    # bytes is only 10.5 vbytes, i.e.
    # ((4 WU/byte * 10 bytes + 1WU/witness byte * 2 witness bytes) / 4)
    #
    # In the simplest 1-input, 1-output case, the max savings I could get by collaborating
    # with an infinite number of participants is ~ 9.5% (10.5 vbytes / 111 vbytes) and
    # each additional input / output I add for myself will decrease my total savings
    # opportunity
    without_cisa_shared = (
        (VBYTES_SHARED / n_participants)*SATS_PER_VBYTE
        + (BYTES_PER_INPUT*n_inputs + BYTES_PER_OUTPUT*n_outputs)*SATS_PER_VBYTE
        + (BYTES_PER_WITNESS_STACK*n_inputs / 4)*SATS_PER_VBYTE
    )
    diff = without_cisa_alone - without_cisa_shared
    pd = (diff / without_cisa_alone) * 100

    # In a half-agg transaction, the single participant pays for the entire transaction
    # with the added benefit that adding inputs is cheaper than before since each the signature
    # for each additional input is now half the size (32 bytes). But this has implications
    # for the collaborative case, as well: if you start with a single input, and then collaborate
    # with others by allowing them to add their own inputs and outputs, we can all split the cost
    # of the aggregated part of the first signature (32 witness bytes).
    #
    # From the example above, our savings opportunity with an infite number of participants is
    # ~ 16.5% ((10.5 vbytes + 8 vbytes) / 111 vbytes)
    half_agg_alone = (tx_vbytes - (n_inputs - 1)*(32/4))*SATS_PER_VBYTE
    half_agg_shared = (
        ((VBYTES_SHARED + 32 / 4) / n_participants)*SATS_PER_VBYTE
        + (BYTES_PER_INPUT * n_inputs + BYTES_PER_OUTPUT*n_outputs)*SATS_PER_VBYTE
        + ((BYTES_PER_WITNESS_STACK * n_inputs - 32*n_inputs) / 4)*SATS_PER_VBYTE
    )
    half_diff = half_agg_alone - half_agg_shared
    half_pd = (half_diff / half_agg_alone)*100

    # In a full-agg transaction, we've now introduced interactivity, but considering a coinjoin is
    # already an interactive protocol this isn't _necessarily_ a downside (but worth mentioning).
    #
    # Same as before, single participant pays for the whole transaction etc, but now our savings
    # opportunity is a full signature. Since the transaction can now be signed with one signature
    # for the whole transaction (regardless of the number of inputs and outputs), we would all split
    # the cost of the single signature (64 witness bytes), along with the shared bytes.
    #
    # From the example above, our savings opportunity with an infinite nuber of participants is
    # now ~ 24% ((10.5 vbytes + 16 vbytes) / 111 bytes). This is now a significant enough savings
    # opportunity that I would almost always be incentivized to collaborate with other participants
    # when creating a transaction. Further more, since each participant pays for their own inputs and
    # outputs, I don't need to prefer certain types of transaction constructions over others to get the
    # savings benefits, which means a coinjoin is just as beneficial as a batch transaction w.r.t to
    # allowing all participants to split the cost of the shared bytes of the transaction.
    #
    # In summary, a full-agg world creates a stronger economic incentive to collaborate with others vs
    # creating a transaction on my own, such that anyone offering a service for coordinating the
    # collaboration can claim to provide both an economic service and privacy service (e.g. by placing
    # additional constraints on the input/output amounts allowed). The savings opportunity is potentially
    # high enough that a user who wouldn't particularly care about the privacy benefits might now
    # be willing to create inputs and outputs in such a way that they can join the coinjoin *only* for
    # the economic benefits
    full_agg_alone = (tx_vbytes - (n_inputs - 1)*(64/4))*SATS_PER_VBYTE
    full_agg_shared = (
        ((VBYTES_SHARED + 64 / 4) / n_participants)*SATS_PER_VBYTE
        + (BYTES_PER_INPUT*n_inputs + BYTES_PER_OUTPUT*n_outputs)*SATS_PER_VBYTE
        + ((BYTES_PER_WITNESS_STACK*n_inputs - 64*n_inputs) / 4)*SATS_PER_VBYTE
    )
    full_diff = full_agg_alone - full_agg_shared
    full_pd = (full_diff / full_agg_alone)*100

    print("Without CISA, I pay:")
    print("    ", without_cisa_alone, "sats by myself")
    print("    ", without_cisa_shared, f"sats with {n_participants - 1} additional participants")
    print("    ", diff, f"sats ({pd} percent)")
    print("")
    print("With CISA half-agg, I pay:")
    print("    ", half_agg_alone, "sats by myself")
    print("    ", half_agg_shared, f"sats with {n_participants - 1} additional participants")
    print("    ", half_diff, f"sats ({half_pd} percent) savings")
    half_alone_diff = without_cisa_shared - half_agg_shared
    half_alone_pd = (half_alone_diff / without_cisa_shared)*100
    print("    ", half_alone_diff, f"sats ({half_alone_pd} percent) savings")
    print("")
    print("With CISA full-agg, I pay:")
    print("    ", full_agg_alone, "sats by myself")
    print("    ", full_agg_shared, f"sats with {n_participants - 1} additional participants")
    print("    ", full_diff, f"sats ({full_pd} percent) savings")
    full_alone_diff = without_cisa_shared - full_agg_shared
    full_alone_pd = (full_alone_diff / without_cisa_shared)*100
    print("    ", full_alone_diff, f"sats ({full_alone_pd} percent) savings")
    print("")

# n_inputs, n_outputs, n_participants
calculate_savings(int(argv[1]), int(argv[2]), int(argv[3]))
