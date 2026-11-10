# GPIO (BCM) pin per lane, in lane order. The number of entries is the
# number of lanes, so a 2-lane track uses two pins and a 6-lane track six.
# Can be overridden at runtime with SLOT_LANE_PINS="18,23" (see lanes.py).
# 2-lane track
LANE_PINS = [18, 23]
# 4-lane track
#LANE_PINS = [18, 23, 24, 25]

# Crossings closer together than this on the same lane are treated as
# sensor bounce / double triggers and ignored. Keep well below the fastest
# realistic lap time.
MIN_LAP_SECONDS = 1.0

# Debug mode: enables verbose debug output. Set to True while troubleshooting.
DEBUG = False
