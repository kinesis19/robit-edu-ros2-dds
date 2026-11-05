# 힌트 카드

막혔을 때만 보세요. 단계마다 힌트가 3단계입니다. 1번으로 안 풀리면 2번, 그래도 안 되면 3번. 몇 번까지 봤는지 보고서에 적어 주세요 (감점 없음, 구두 질문 참고용).

## 1단계

1. `ros2 topic list` 는 **현재 `ROS_DOMAIN_ID`** 의 토픽만 보여 줍니다. 도메인을 바꿔 가며 반복하면 됩니다.
2. 셸 반복문이나 Python `subprocess` 로 10~95를 돌리세요. `ros2 topic list --help` 에서 데몬과 발견 대기 시간 옵션을 확인하세요. 발견에는 시간이 걸립니다.
3. 도메인마다 `ROS_DOMAIN_ID=$d ros2 topic list --no-daemon` 을 실행하고 이름이 `bb_` 로 시작하는 토픽을 찾으세요. 응답은 `ros2 topic pub` 으로 보내되, 발행자가 구독자를 찾기 전에 끝나지 않도록 `-r` 옵션이나 `-t` 옵션을 확인하세요.
4. 스캔에서 안 보이면 로봇이 아니라 대기 시간이 짧은 것일 수 있다. --spin-time 4 이상으로 하고, 의심되는 도메인은 한 번 더 조회한다.

## 2단계

1. `ros2 topic info -v <토픽>` 에서 발행자의 **Reliability** 와 **Durability** 를 보세요.
2. 3장 호환 규칙을 떠올리세요. 구독자가 요구하는 것을 발행자가 제공할 수 있어야 합니다. `ros2 topic echo` 는 값을 훑어보는 데 쓸 수 있지만, 판정은 **직접 만든 노드**만 인정합니다.
3. rclpy 에서 `QoSProfile(reliability=..., durability=..., history=..., depth=...)` 를 만들어 `create_subscription` 의 마지막 인자로 넘기세요. config 토픽은 `transient_local`, stream 토픽은 `best_effort` 로 구독합니다. 노드는 해당 도메인(`ROS_DOMAIN_ID`)에서 실행해야 합니다. 응답을 `ros2 topic pub` 으로 보낼 때는 1단계처럼 `-r` 이나 `-t` 로 구독자를 찾을 시간을 주세요.

## 3단계

1. Cyclone DDS 공식 문서의 **Configuration** 페이지를 보세요. 요소는 `General`, `Discovery`, `Tracing` 아래에 있습니다.
2. 찾을 요소: `AllowMulticast`, `Peers` 와 `Peer`, `MaxAutoParticipantIndex`, `Tracing` 의 `Verbosity` 와 `OutputFile`. 루트는 `CycloneDDS`, 그 아래 `Domain` 입니다.
3. 구조: `CycloneDDS > Domain > (General > AllowMulticast), (Discovery > Peers > Peer address=..., MaxAutoParticipantIndex), (Tracing > Verbosity, OutputFile)`. 값은 `check3` 가 출력하는 요구사항에서 가져오세요. 설정이 읽혔는지는 로그 앞부분에서 확인합니다.

## 4단계

1. talker 가 있는 도메인을 알아내려면 2단계 신호를 다시 읽어 보세요.
2. `ros2 topic list`, `ros2 topic info -v`, `ros2 topic type` 으로 talker 쪽 도메인·토픽 이름·타입·QoS 를 각각 확인한 뒤, `listener.env` 의 네 값과 하나씩 비교하세요.
3. 네 값 중 2~3개가 틀립니다. 도메인이 틀리면 서로 **존재 자체를 못 봅니다.** 나머지는 서로를 본 뒤 **짝지어지지 않는** 문제입니다. 하나를 고치면 다음 문제가 드러날 수 있으니 하나씩 고치세요.
