"""Money is whole paise (int). Never floats."""


def rupees(paise: int) -> str:
    """12345600 -> '₹1,23,456' (Indian grouping), paise dropped when zero."""
    whole, part = divmod(int(paise), 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    return "₹" + s + (f".{part:02d}" if part else "")
