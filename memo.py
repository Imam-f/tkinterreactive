# memo.py
def shallow_equal(a, b):
    if a is b:
        return True
    if len(a) != len(b):
        return False
    return all(x == y for x, y in zip(a, b))

def create_memo():
    last_deps = []
    has = False
    last_val = None

    def compute(fn, deps):
        nonlocal last_deps, has, last_val
        if not has or not shallow_equal(last_deps, deps):
            last_val = fn()
            last_deps = list(deps)
            has = True
        return last_val

    return compute

def memo_key_from(deps):
    return "|".join(str(d) for d in deps)