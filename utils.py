import json


def log(*args, **kwargs):
    print(*args, **kwargs)


def byte_to_signed_int(byte):
    if byte > 127:
        return -1 * (256 - byte)
    else:
        return byte


def formatted_nestest_log():
    with open('nestest.log', 'r') as f:
        d = f.read()
    txt_list = d.strip().split('\n')
    logs = []
    for t in txt_list:
        r = []
        # e = t.split(' ')
        pc = t[0:4]
        f_pc = int(pc, 16)
        op = t[6:8]
        f_op = int(op, 16)
        name = t[16:20]
        a = t[50:52]
        f_a = int(a, 16)
        x = t[55:57]
        f_x = int(x, 16)
        y = t[60:62]
        f_y = int(y, 16)
        p = t[65:67]
        f_p = int(p, 16)
        sp = t[71:73]
        f_sp = int(sp, 16)
        r.append(f_pc)
        r.append(f_op)
        r.append(f_a)
        r.append(f_x)
        r.append(f_y)
        r.append(f_p)
        r.append(f_sp)
        log(pc, op, name, a, x, y, p, sp)
        # r = list(filter(lambda s: s != '', e))
        # r = r[:-1]
        logs.append(r)
    with open('f_nestest.json', 'w') as f:
        s = json.dumps(logs)
        f.write(s)
    log('done!')
    # return logs
