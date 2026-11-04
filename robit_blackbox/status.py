"""`status`: 진행 확인, `report`: 제출용 요약."""
import argparse
import sys

from robit_blackbox import core

STAGES = {1: '정찰', 2: 'QoS', 3: 'Cyclone 설정', 4: '고장 진단 (도전)'}


def _table(name):
    done = {e['stage']: e['t'] for e in core.read_ledger(name)}
    lines = []
    for n, title in STAGES.items():
        mark = '통과  ' + done[n] if n in done else '-'
        lines.append('  %d단계 %-18s %s' % (n, title, mark))
    return lines


def main_status(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])
    name = core.clean_name(a.name)
    print('이름: %s' % name)
    print('\n'.join(_table(name)))
    print('  5단계 자유 탐구        보고서로 제출')
    if not core.verify_chain(name):
        print('\n⚠ 기록 파일이 올바르지 않습니다 (수정된 흔적).')
    return 0


def main_report(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])
    name = core.clean_name(a.name)
    entries = core.read_ledger(name)
    head = entries[-1]['hash'] if entries else '-'
    print('=== ROBIT 블랙박스 제출 요약 ===')
    print('이름: %s (id %s)' % (name, core.slug(name)))
    print('\n'.join(_table(name)))
    print('기록 검증: %s' % ('정상' if core.verify_chain(name) else '이상 있음'))
    print('기록 해시: %s' % head)
    print('이 출력을 보고서 맨 위에 붙여 넣으세요.')
    return 0
