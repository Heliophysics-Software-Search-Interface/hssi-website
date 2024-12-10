(printf '%04x%04x-%04x-%04x-%04x-%04x%04x%04x' \
        $RANDOM $RANDOM \
        $RANDOM \
        $((RANDOM & 0x0fff | 0x4000)) \
        $((RANDOM & 0x3fff | 0x8000)) \
        $RANDOM $RANDOM $RANDOM)