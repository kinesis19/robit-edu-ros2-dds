"""`ros2 run robit_blackbox robot --name <이름>`: 블랙박스 로봇을 켠다."""
import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
import time

from robit_blackbox import core


def _child_env(domain):
    env = dict(os.environ)
    for k in ('CYCLONEDDS_URI', 'ROS_STATIC_PEERS', 'ROS_LOCALHOST_ONLY',
              'FASTRTPS_DEFAULT_PROFILES_FILE', 'FASTDDS_DEFAULT_PROFILES_FILE'):
        env.pop(k, None)
    env['RMW_IMPLEMENTATION'] = 'rmw_fastrtps_cpp'
    env['ROS_DOMAIN_ID'] = str(domain)
    # 같은 망의 다른 사람 로봇과 섞이지 않도록 이 PC 안으로 제한한다.
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    return env


def main(argv=None):
    ap = argparse.ArgumentParser(description='ROBIT 블랙박스 로봇')
    ap.add_argument('--name', required=True, help='내 이름 (제출물에 표시됨)')
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])
    name = core.clean_name(args.name)

    try:
        import rclpy  # noqa: F401
    except ImportError:
        print('rclpy 를 찾을 수 없습니다. `source /opt/ros/jazzy/setup.bash` 를 먼저 하세요.')
        return 1

    sc = core.load_scenario(name)
    sdir = core.state_dir(name)
    lock_f = open(os.path.join(sdir, 'robot.lock'), 'w')
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print('이름 "%s" 의 로봇이 이미 실행 중입니다. 다른 터미널의 로봇을 종료(Ctrl+C)한 뒤 다시 켜세요.' % name)
        return 1
    env_path = os.path.join(sdir, 'listener.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(core.listener_env_text(sc))

    procs = {}
    lock = threading.Lock()
    seen = {e['stage'] for e in core.read_ledger(name)}

    def pump(stage_key, p):
        for line in p.stdout:
            line = line.rstrip('\n')
            if line.startswith('@@CLEAR'):
                n = int(line.split()[1])
                with lock:
                    added = core.add_ledger(name, n)
                    seen.add(n)
                if added:
                    print('\n★ %d단계 통과! 기록되었습니다.\n' % n, flush=True)
            elif line.strip():
                print(line, flush=True)

    def spawn(key, stage, domain, extra=None):
        cfg = {'scenario': sc}
        if extra:
            cfg.update(extra)
        p = subprocess.Popen(
            [sys.executable, '-m', 'robit_blackbox.nodes', stage],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=_child_env(domain))
        p.stdin.write(json.dumps(cfg) + '\n')
        p.stdin.flush()
        threading.Thread(target=pump, args=(key, p), daemon=True).start()
        with lock:
            procs[key] = p

    def start_listener():
        try:
            env = core.read_env_file(env_path)
        except OSError:
            env = {}
        try:
            dom = int(env.get('LISTENER_DOMAIN', sc['d4']))
        except ValueError:
            dom = sc['d4']
        spawn('listener4', 'listener4', dom, {'env': env})

    def stop(*_a):
        with lock:
            for p in procs.values():
                if p.poll() is None:
                    p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    spawn('s1', 's1', sc['d1'])
    spawn('s2', 's2', sc['d2'])
    spawn('talker4', 'talker4', sc['d4'])
    start_listener()

    print('블랙박스 로봇이 켜졌습니다. (이름: %s)' % name)
    print('  진행 확인     : ros2 run robit_blackbox status --name "%s"' % name)
    print('  listener 설정 : %s  (4단계)' % env_path)
    print('이 터미널은 그대로 두세요. 종료는 Ctrl+C. 같은 이름으로 다시 켜면 진행이 이어집니다.')

    mtime = os.path.getmtime(env_path)
    while True:
        time.sleep(1.0)
        try:
            mt = os.path.getmtime(env_path)
        except OSError:
            continue
        # 다른 프로세스(check3 등)가 기록한 단계도 이 터미널에 알린다.
        with lock:
            new = [e['stage'] for e in core.read_ledger(name) if e['stage'] not in seen]
            seen.update(new)
        for n in new:
            print('\n★ %d단계 통과! 기록되었습니다. (check 결과)\n' % n, flush=True)
        if mt != mtime:
            mtime = mt
            with lock:
                p = procs.get('listener4')
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(3)
                except subprocess.TimeoutExpired:
                    p.kill()
            start_listener()
            print('listener.env 변경을 감지해 listener 를 다시 시작했습니다.', flush=True)
        for k in ('s1', 's2', 'talker4'):
            with lock:
                p = procs.get(k)
            if p is not None and p.poll() is not None:
                print('내부 프로세스 %s 가 종료되었습니다. 로봇을 다시 켜 주세요.' % k)
                stop()


if __name__ == '__main__':
    sys.exit(main())
