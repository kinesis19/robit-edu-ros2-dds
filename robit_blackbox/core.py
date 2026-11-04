"""공용 로직: 시나리오 생성/저장, 진행 기록(ledger).

이 repo 에는 정답이 없다. 시나리오(도메인, 토픽, 단어 등)는 로봇을 처음 켤 때
무작위로 만들어져 학생 PC 에만 저장된다.
"""
import base64
import datetime
import hashlib
import json
import os
import random

BASE = os.path.expanduser('~/.ros/robit_blackbox')
WORDS = ['ALPHA', 'BRAVO', 'CEDAR', 'DELTA', 'EMBER', 'FALCON', 'GLACIER',
         'HARBOR', 'IVORY', 'JUNIPER', 'KESTREL', 'LANTERN', 'MARBLE', 'NEBULA']
KNOBS = ['DOMAIN', 'TOPIC', 'TYPE', 'RELIABILITY']


def clean_name(name):
    return ' '.join(str(name).split())


def slug(name):
    return hashlib.sha256(clean_name(name).encode()).hexdigest()[:8]


def state_dir(name):
    path = os.path.join(BASE, slug(name))
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------- 시나리오
def _key(name):
    return hashlib.sha256(('bb-scenario|' + clean_name(name)).encode()).digest()


def _xor(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _new_scenario():
    r = random.SystemRandom()
    d1, d2, d4 = r.sample(range(10, 96), 3)
    hexs = '0123456789abcdef'
    nfault = r.choice([2, 3])
    return {
        'd1': d1, 'd2': d2, 'd4': d4,
        'pfx': 'bb_' + ''.join(r.choice(hexs) for _ in range(4)),
        'c1': '%s-%d' % (r.choice(WORDS), r.randint(1000, 9999)),
        'w': ''.join(r.choice(hexs) for _ in range(4)),
        'v': ''.join(r.choice(hexs) for _ in range(4)),
        'talker_type': r.choice(['String', 'Int32']),
        'faults': r.sample(KNOBS, nfault),
    }


def load_scenario(name):
    path = os.path.join(state_dir(name), 'scenario.bin')
    if os.path.exists(path):
        raw = base64.b64decode(open(path, 'rb').read())
        return json.loads(_xor(raw, _key(name)).decode())
    sc = _new_scenario()
    raw = _xor(json.dumps(sc).encode(), _key(name))
    with open(path, 'wb') as f:
        f.write(base64.b64encode(raw))
    os.chmod(path, 0o600)
    return sc


def listener_env_text(sc):
    other = 'Int32' if sc['talker_type'] == 'String' else 'String'
    f = set(sc['faults'])
    dom = sc['d4'] + 1 if 'DOMAIN' in f else sc['d4']
    topic = '/%s/command' % sc['pfx'] if 'TOPIC' in f else '/%s/cmd' % sc['pfx']
    typ = other if 'TYPE' in f else sc['talker_type']
    rel = 'reliable' if 'RELIABILITY' in f else 'best_effort'
    return ('# 로봇 listener 의 설정. 이 파일을 고치면 listener 가 자동으로 다시 시작된다.\n'
            '# 값 중 일부가 틀려 있다. 로봇이 보내는 신호를 조사해서 고쳐라.\n'
            'LISTENER_DOMAIN=%d\n'
            'LISTENER_TOPIC=%s\n'
            'LISTENER_TYPE=%s\n'
            'LISTENER_RELIABILITY=%s\n' % (dom, topic, typ, rel))


def read_env_file(path):
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            out[k.strip()] = v.strip()
    return out


# ---------------------------------------------------------------- 진행 기록
def _ledger_path(name):
    return os.path.join(state_dir(name), 'ledger.jsonl')


def read_ledger(name):
    path = _ledger_path(name)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return [json.loads(x) for x in f if x.strip()]


def _hash(prev, name, stage, t):
    return hashlib.sha256(('%s|%s|%s|%s' % (prev, clean_name(name), stage, t)).encode()).hexdigest()[:16]


def add_ledger(name, stage):
    """단계 통과를 기록한다. 이미 기록된 단계면 False."""
    entries = read_ledger(name)
    if any(e['stage'] == stage for e in entries):
        return False
    prev = entries[-1]['hash'] if entries else '0' * 16
    t = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    e = {'stage': stage, 't': t, 'prev': prev, 'hash': _hash(prev, name, stage, t)}
    with open(_ledger_path(name), 'a', encoding='utf-8') as f:
        f.write(json.dumps(e, ensure_ascii=False) + '\n')
    return True


def verify_chain(name):
    prev = '0' * 16
    for e in read_ledger(name):
        if e['prev'] != prev or e['hash'] != _hash(prev, name, e['stage'], e['t']):
            return False
        prev = e['hash']
    return True
