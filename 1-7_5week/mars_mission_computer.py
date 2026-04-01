import time


SENSOR_DATA_FILE = "sensor_data.json"
READ_INTERVAL = 5
AVERAGE_INTERVAL = 300


def parse_json_file(filepath):
    """flat JSON 파일을 직접 파싱한다."""
    result = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.strip().strip("{}")
        lines = content.split("\n")
        for line in lines:
            line = line.strip().rstrip(",")
            if not line:
                continue
            colon_idx = line.index(":")
            key = line[:colon_idx].strip().strip('"')
            value = line[colon_idx + 1:].strip()
            try:
                result[key] = float(value) if "." in value else int(value)
            except ValueError:
                result[key] = value.strip('"')
    except FileNotFoundError:
        print(f"[경고] '{filepath}' 파일을 찾을 수 없습니다.")
    return result


def dict_to_json_str(data, indent=4):
    """dict를 JSON 형식 문자열로 변환한다."""
    lines = ["{"]
    items = list(data.items())
    for i, (key, value) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        pad = " " * indent
        if value is None:
            lines.append(f'{pad}"{key}": null{comma}')
        elif isinstance(value, bool):
            lines.append(f'{pad}"{key}": {str(value).lower()}{comma}')
        elif isinstance(value, (int, float)):
            lines.append(f'{pad}"{key}": {value}{comma}')
        else:
            lines.append(f'{pad}"{key}": "{value}"{comma}')
    lines.append("}")
    return "\n".join(lines)


class DummySensor:
    """JSON 파일에서 센서 데이터를 읽어오는 더미 센서 클래스."""

    def get_env_data(self):
        return parse_json_file(SENSOR_DATA_FILE)


class MissionComputer:
    """화성 기지 환경 데이터를 수집하고 출력하는 미션 컴퓨터 클래스."""

    def __init__(self):
        self.env_values = {
            "mars_base_internal_temperature": None,
            "mars_base_external_temperature": None,
            "mars_base_internal_humidity": None,
            "mars_base_external_illuminance": None,
            "mars_base_internal_co2": None,
            "mars_base_internal_oxygen": None,
        }
        self.ds = DummySensor()
        self._sum_values = {key: 0.0 for key in self.env_values}
        self._count = 0
        self._last_avg_time = None

    def _update_env_values(self, sensor_data):
        """센서 데이터를 env_values와 누적합에 반영한다."""
        for key in self.env_values:
            if key in sensor_data and sensor_data[key] is not None:
                self.env_values[key] = sensor_data[key]
                self._sum_values[key] += sensor_data[key]
        self._count += 1

    def _print_average(self):
        """누적된 값의 5분 평균을 출력한다."""
        if self._count == 0:
            return
        avg = {
            key: round(self._sum_values[key] / self._count, 2)
            for key in self._sum_values
        }
        print("\n[5분 평균값]")
        print(dict_to_json_str(avg))
        print("=" * 40 + "\n")

    def _reset_average(self):
        """평균 계산용 누적 데이터를 초기화한다."""
        self._sum_values = {key: 0.0 for key in self.env_values}
        self._count = 0

    def get_sensor_data(self):
        """센서 데이터를 읽어 출력하고, 5분마다 평균을 출력한다."""
        print("미션 컴퓨터 가동 시작.")
        print("다음 사이클로 넘어가려면 Enter, 종료하려면 q 입력\n")

        self._last_avg_time = time.time()

        while True:
            # 센서 읽기 및 출력
            sensor_data = self.ds.get_env_data()
            self._update_env_values(sensor_data)
            print(dict_to_json_str(self.env_values))
            print("-" * 40)

            # 5분 평균 체크
            if time.time() - self._last_avg_time >= AVERAGE_INTERVAL:
                self._print_average()
                self._reset_average()
                self._last_avg_time = time.time()

            # 키 입력으로 정지 여부 확인
            user_input = input("▶ ").strip().lower()
            if user_input == "q":
                print("System stopped....")
                break

            time.sleep(READ_INTERVAL)


RunComputer = MissionComputer()
RunComputer.get_sensor_data()

# **핵심 구조 변화**

# [이전] sleep(5) 중에 키 감지 → 불가능 → threading 필요
# [현재] 출력 → input() 대기 → sleep(5) → 반복
#          ↑ 여기서 자연스럽게 키 입력 처리