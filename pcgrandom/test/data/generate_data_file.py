"""
Code to generate a JSON "fingerprint" for a generator. This is used for
reproducibility testing, as well as checking portability of pickles.
"""
from pcgrandom.test.fingerprint import write_fingerprints
from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0


if __name__ == '__main__':
    write_fingerprints(
        generators=[
            PCG_XSH_RR_V0(seed=12345),
            PCG_XSL_RR_V0(seed=41509),
        ],
        filename='generator_fingerprints.json',
    )
