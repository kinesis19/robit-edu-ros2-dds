"""로봇의 각 단계 노드. robot.py 가 자식 프로세스로 실행한다.

설정은 부모가 stdin 으로 JSON 한 줄을 넘겨 준다 (명령줄/환경변수에 남기지 않기 위해).
단계 통과는 stdout 에 '@@CLEAR <단계>' 를 출력해 부모에게 알린다.
"""
import json
import os
import random
import sys


def _clear(stage):
    print('@@CLEAR %d' % stage, flush=True)


def run(stage, cfg):
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                           ReliabilityPolicy)
    from std_msgs.msg import Int32, String

    sc = cfg['scenario']
    pfx = sc['pfx']

    def qos(rel, dur, depth):
        return QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE if rel == 'reliable' else ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL if dur == 'transient_local' else DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST, depth=depth)

    rclpy.init()
    node = Node('bb_' + stage)
    state = {'done': False}

    if stage == 's1':
        pub = node.create_publisher(String, '/%s/telemetry' % pfx, qos('reliable', 'volatile', 10))
        x = y = 0.0

        def tick():
            nonlocal x, y
            x += random.uniform(-0.1, 0.1)
            y += random.uniform(-0.1, 0.1)
            m = String()
            m.data = ('BB1 pos=(%.2f,%.2f) | 챌린지: %s | 이 단어를 그대로 /%s/ack 로 보내라 | 다음 신호: 도메인 %d'
                      % (x, y, sc['c1'], pfx, sc['d2']))
            pub.publish(m)

        def on_ack(m):
            if not state['done'] and m.data.strip() == sc['c1']:
                state['done'] = True
                _clear(1)

        node.create_subscription(String, '/%s/ack' % pfx, on_ack, 10)
        node.create_timer(1.0, tick)

    elif stage == 's2':
        cfg_pub = node.create_publisher(String, '/%s/config' % pfx, qos('reliable', 'transient_local', 1))
        stream = node.create_publisher(String, '/%s/stream' % pfx, qos('best_effort', 'volatile', 5))
        m = String()
        m.data = ('BB2-A word=%s | 스트림은 /%s/stream | 각 메시지의 word= 뒤 값 두 개를 A-B 순서로 "-" 로 이어 /%s/answer 로 보내라 '
                  '(구독 노드가 켜져 있는 동안) | 다음 신호: 도메인 %d의 /%s/cmd'
                  % (sc['w'], pfx, pfx, sc['d4'], pfx))
        cfg_pub.publish(m)  # 한 번만 발행
        n = 0

        def tick():
            nonlocal n
            n += 1
            mm = String()
            mm.data = 'BB2-B word=%s n=%d' % (sc['v'], n)
            stream.publish(mm)

        def ok_endpoint(topic, want_rel=None, want_dur=None):
            try:
                infos = node.get_subscriptions_info_by_topic(topic)
            except Exception:
                return False
            for ep in infos:
                if ep.node_name.startswith('_ros2cli'):
                    continue  # CLI 가 아니라 직접 만든 노드여야 한다
                q = ep.qos_profile
                if want_rel is not None and q.reliability != want_rel:
                    continue
                if want_dur is not None and q.durability != want_dur:
                    continue
                return True
            return False

        def on_answer(m):
            if state['done']:
                return
            if m.data.strip() != '%s-%s' % (sc['w'], sc['v']):
                print('[2단계] 응답 값이 맞지 않습니다. 형식: config 의 word= 값, 하이픈, stream 의 word= 값.', flush=True)
                return
            a = ok_endpoint('/%s/config' % pfx, want_dur=DurabilityPolicy.TRANSIENT_LOCAL)
            b = ok_endpoint('/%s/stream' % pfx, want_rel=ReliabilityPolicy.BEST_EFFORT)
            if a and b:
                state['done'] = True
                _clear(2)
            else:
                print('[2단계] 값은 맞습니다. 하지만 직접 만든 구독 노드가 두 토픽을 알맞은 QoS 로 '
                      '구독 중인지 확인되지 않았습니다 (config %s, stream %s). 응답을 보낼 때 노드가 켜져 있어야 합니다.'
                      % ('OK' if a else 'X', 'OK' if b else 'X'), flush=True)

        node.create_subscription(String, '/%s/answer' % pfx, on_answer, 10)
        node.create_timer(0.1, tick)

    elif stage == 'talker4':
        msg_t = String if sc['talker_type'] == 'String' else Int32
        pub = node.create_publisher(msg_t, '/%s/cmd' % pfx, qos('best_effort', 'volatile', 5))
        n = 0

        def tick():
            nonlocal n
            n += 1
            m = msg_t()
            if msg_t is String:
                m.data = 'cmd=hold n=%d' % n
            else:
                m.data = n
            pub.publish(m)

        node.create_timer(0.5, tick)

    elif stage == 'listener4':
        env = cfg['env']
        msg_t = String if env.get('LISTENER_TYPE', 'String') == 'String' else Int32
        count = {'n': 0}

        def cb(_m):
            count['n'] += 1
            if count['n'] >= 5 and not state['done']:
                state['done'] = True
                _clear(4)

        node.create_subscription(msg_t, env.get('LISTENER_TOPIC', '/none'), cb,
                                 qos(env.get('LISTENER_RELIABILITY', 'reliable'), 'volatile', 10))

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main():
    stage = sys.argv[1]
    cfg = json.loads(sys.stdin.readline())
    run(stage, cfg)


if __name__ == '__main__':
    main()
