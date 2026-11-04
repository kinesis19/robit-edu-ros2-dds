# robit-edu-ros2-dds

ROBIT 인턴 ROS 2 심화 교육(미들웨어/DDS) **Day 1 미션 과제**입니다.
내 PC 안에 "블랙박스 로봇"이 켜지고, 그 로봇이 어느 도메인·토픽·QoS로 말하는지는 **실행할 때마다 무작위**로 정해집니다. 교육 자료로 공부한 도구로 조사해서 연결하는 과제입니다.

- 이 repo에는 **정답이 들어 있지 않습니다.** 시나리오는 로봇을 처음 켤 때 내 PC에서 만들어집니다.
- 단계 통과는 로봇이 내 동작을 직접 관찰해서 판정하고, 기록을 남깁니다.
- 과제 상세는 [MISSION.md](MISSION.md), 막혔을 때는 [HINTS.md](HINTS.md)를 보세요.

## 준비물

- Ubuntu 24.04 + ROS 2 Jazzy (desktop)
- `git`, `colcon` (`sudo apt install git python3-colcon-common-extensions`)
- (3단계) Cyclone DDS: 교육 자료 "Cyclone DDS 준비" 슬라이드 참고

## 설치 (처음 한 번)

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/<GitHub 계정>/robit-edu-ros2-dds.git
cd ~/ros2_ws
colcon build --packages-select robit_blackbox
source install/setup.bash
```

> `~/.bashrc` 에 `source /opt/ros/jazzy/setup.bash` 와 `source ~/ros2_ws/install/setup.bash` 를 넣어 두면 새 터미널마다 다시 입력하지 않아도 됩니다.

## 사용법

터미널 **여러 개**를 씁니다. 새 터미널마다 아래 두 줄을 먼저 실행하세요 (`.bashrc` 에 넣었다면 생략).

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

### 1. 로봇 켜기 (터미널 A, 그대로 켜 둠)

```bash
ros2 run robit_blackbox robot --name "홍길동"
```

- `--name` 은 본인 이름입니다 (한글 가능). **끝까지 같은 이름**을 쓰세요.
- 종료는 `Ctrl+C`. 같은 이름으로 다시 켜면 같은 시나리오와 진행 기록이 이어집니다.
- 로봇을 켜면 4단계용 설정 파일 위치(`listener.env`)가 화면에 나옵니다.

### 2. 진행 확인

```bash
ros2 run robit_blackbox status --name "홍길동"
```

### 3. 3단계 검사 (Cyclone 설정 파일)

```bash
ros2 run robit_blackbox check3 --name "홍길동"                 # 기본: ~/cyclonedds_bb.xml
ros2 run robit_blackbox check3 --name "홍길동" --xml 경로.xml
```

처음 실행하면 **내 이름에 맞춘 요구사항**이 출력됩니다. 그 요구사항대로 XML을 써서 다시 실행하세요.

### 4. 제출용 요약

```bash
ros2 run robit_blackbox report --name "홍길동"
```

출력을 보고서 맨 위에 붙여 넣습니다.

## 파일 위치

| 위치 | 내용 |
|---|---|
| `~/.ros/robit_blackbox/<id>/` | 내 시나리오, 진행 기록, `listener.env` |
| `~/.ros/robit_blackbox/<id>/listener.env` | 4단계에서 고치는 파일 |

`<id>` 는 이름에서 만들어진 8자리 값이며, `status`/`report` 출력에 나옵니다.
처음부터 다시 하려면 해당 폴더를 지우고 로봇을 다시 켜세요 (진행 기록도 지워집니다).

## 규칙

- AI와 인터넷을 써도 됩니다. 단, **내 PC에서 직접 확인한 결과**만 근거가 됩니다.
- 로봇의 소스, 프로세스, 상태 파일을 들여다봐서 답을 얻지 마세요. 조사하는 것이 과제입니다.
- 모르는 것은 공식 문서와 `--help` 에서 찾습니다.

## 문제 해결

| 증상 | 확인 |
|---|---|
| `Package 'robit_blackbox' not found` | `source ~/ros2_ws/install/setup.bash` 를 했는지 |
| `rclpy 를 찾을 수 없습니다` | `source /opt/ros/jazzy/setup.bash` 를 했는지 |
| `colcon build` 실패 | `sudo apt install python3-colcon-common-extensions`, ROS를 source 한 상태인지 |
| 로봇 신호가 안 보임 | 새 터미널의 `env | grep -E "ROS|RMW|CYCLONE"` 로 옛 설정이 남았는지, `ros2 daemon stop` |
| 이름을 바꾸고 싶음 | 이름이 바뀌면 새 시나리오가 시작됩니다. 기존 이름으로 계속하세요 |
| 3단계 통신 테스트 실패 | Cyclone 설치 여부 (`ros2 pkg prefix rmw_cyclonedds_cpp`), XML 문법, 방화벽 |

## zsh 사용자

`source /opt/ros/jazzy/setup.zsh`, `source ~/ros2_ws/install/setup.zsh`, 설정 파일은 `~/.zshrc` 입니다.
