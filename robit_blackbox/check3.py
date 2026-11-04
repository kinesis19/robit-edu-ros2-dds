"""`check3`: 3단계(Cyclone 설정 파일) 검사.
"""
import argparse
import hashlib
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

from robit_blackbox import core


def spec(name):
    h = hashlib.sha256(('bb3|' + core.clean_name(name)).encode()).hexdigest()
    return {
        'domain': 10 + int(h[:4], 16) % 86,
        'max_idx': 5 + int(h[4:6], 16) % 6,
        'log': '/tmp/bb3_%s.log' % core.slug(name),
    }


def _find(pattern, text):
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else None


def main(argv=None):
    ap = argparse.ArgumentParser(description='3단계: Cyclone 설정 파일 검사')
    ap.add_argument('--name', required=True)
    ap.add_argument('--xml', default='~/cyclonedds_bb.xml', help='검사할 XML (기본 ~/cyclonedds_bb.xml)')
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])
    name = core.clean_name(a.name)
    sp = spec(name)
    xml_path = os.path.abspath(os.path.expanduser(a.xml))

    print('[%s] 3단계 요구사항' % name)
    print('  - 검사는 ROS_DOMAIN_ID=%d 에서 실행된다 (도구가 알아서 설정)' % sp['domain'])
    print('  - Peers 에 127.0.0.1 이 있다')
    print('  - AllowMulticast 는 false 또는 spdp')
    print('  - MaxAutoParticipantIndex 는 %d' % sp['max_idx'])
    print('  - Tracing 의 Verbosity 를 지정하고 OutputFile 은 %s' % sp['log'])
    print()
    if not os.path.exists(xml_path):
        print('[NG] 설정 파일이 없습니다: %s' % xml_path)
        return 1
    text = open(xml_path, encoding='utf-8').read()
    ok = True

    def check(title, cond):
        nonlocal ok
        print('[%s] %s' % ('OK' if cond else 'NG', title))
        ok = ok and cond

    try:
        ET.fromstring(text)
        well = True
    except ET.ParseError as e:
        well = False
        print('   XML 오류:', e)
    check('XML 형식이 올바르다', well)
    mc = _find(r'<AllowMulticast>\s*([^<\s]+)\s*</AllowMulticast>', text)
    check('AllowMulticast 가 false 또는 spdp (현재 %s)' % mc, mc in ('false', 'spdp'))
    check('Peers 에 127.0.0.1 이 있다',
          bool(re.search(r'<Peer\b[^>]*address\s*=\s*["\']127\.0\.0\.1["\']', text)))
    mi = _find(r'<MaxAutoParticipantIndex>\s*(\d+)\s*</MaxAutoParticipantIndex>', text)
    check('MaxAutoParticipantIndex = %d (현재 %s)' % (sp['max_idx'], mi), mi == str(sp['max_idx']))
    of = _find(r'<OutputFile>\s*([^<]+?)\s*</OutputFile>', text)
    check('Tracing OutputFile = %s' % sp['log'], of == sp['log'])
    check('Tracing Verbosity 가 있다', bool(re.search(r'<Verbosity>\s*\S+\s*</Verbosity>', text)))
    if not ok:
        print('\n구조 점검에서 실패했습니다. 통신 테스트는 건너뜁니다.')
        return 1
    if not shutil.which('ros2'):
        print('ros2 를 찾지 못했습니다. `source /opt/ros/jazzy/setup.bash` 를 하세요.')
        return 1

    try:
        os.remove(sp['log'])
    except OSError:
        pass
    env = dict(os.environ)
    env.update({
        'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp',
        'ROS_DOMAIN_ID': str(sp['domain']),
        'CYCLONEDDS_URI': 'file://' + xml_path,
        'RCUTILS_LOGGING_USE_STDOUT': '1',
        'RCUTILS_LOGGING_BUFFERED_STREAM': '0',
    })
    env.pop('ROS_STATIC_PEERS', None)
    env.pop('ROS_AUTOMATIC_DISCOVERY_RANGE', None)
    print('\nCyclone + 당신의 XML 로 talker/listener 를 최대 25초간 돌려 봅니다...')
    kw = dict(env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lis = subprocess.Popen(['ros2', 'run', 'demo_nodes_cpp', 'listener'], **kw)
    tal = subprocess.Popen(['ros2', 'run', 'demo_nodes_cpp', 'talker'], **kw)
    q = queue.Queue()

    def reader():
        for line in lis.stdout:
            q.put(line)

    threading.Thread(target=reader, daemon=True).start()
    heard = False
    t0 = time.time()
    while time.time() - t0 < 25 and not heard:
        try:
            if 'I heard' in q.get(timeout=1):
                heard = True
        except queue.Empty:
            pass
    for p in (tal, lis):
        p.terminate()
    time.sleep(1.0)
    check('listener 가 talker 메시지를 받았다', heard)
    logged = os.path.exists(sp['log']) and os.path.getsize(sp['log']) > 0
    check('Tracing 로그 파일이 생겼다', logged)
    if heard and logged:
        core.add_ledger(name, 3)
        print('\n★ 3단계 통과! 기록되었습니다. 보고서에는 XML 과 로그에서 찾은 근거 2~3줄을 함께 넣으세요.')
        return 0
    print('\n실패한 항목을 고친 뒤 다시 실행하세요.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
