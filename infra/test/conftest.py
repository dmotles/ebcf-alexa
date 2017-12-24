import sys
import os

# XXX HACK HACK HACK - infra is not shipped with the pkg,
# so its never installed. It needs to be manually added to the
# path for testing.
sys.path.append(
    os.path.dirname(  # infra dir
        os.path.dirname(  # test dir
            os.path.realpath(__file__) # current file location
        )
    )
)
