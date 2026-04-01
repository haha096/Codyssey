import time


# 스크립트 파일의 절대 경로에서 디렉토리 부분만 추출
# __file__ : 현재 실행 중인 스크립트의 전체 경로
# -> 파일의 경로를 모듈없이 읽기 위해 __file__ 사용
# replace("\\", "/") : 윈도우 역슬래시를 슬래시로 통일
# rsplit("/", 1)[0] : 마지막 "/" 기준으로 분리 후 앞부분(폴더 경로)만 추출
script_dir = __file__.replace("\\", "/").rsplit("/", 1)[0]

# sensor_data.json 파일 경로를 스크립트 기준으로 설정
# os 모듈 없이 문자열 연산만으로 경로를 조합
# 실행 위치에 상관없이 항상 스크립트와 같은 폴더에서 JSON을 찾음
SENSOR_DATA_FILE = script_dir + "/sensor_data.json"

# 수행과제 : 5초에 한 번씩 반복 동작
READ_INTERVAL = 5

# 보너스 과제 : 5분에 한 번씩 각 환경값의 평균 출력
# 300초(5분)를 상수로 정의하여 관리
AVERAGE_INTERVAL = 300


# JSON파일 파싱 함수)
# 문제 정의
# - 제약사항 : json 모듈을 포함한 시간 외 라이브러리 사용 불가
# - 센서 데이터를 외부 JSON 파일에서 읽어오려면 직접 파싱 필요
#
# 기술 구현
# - 파일을 줄 단위로 읽어 "키": 값 형태를 직접 분리
# - 콜론(:) 위치를 기준으로 key / value 추출 -> 딕셔너리 형태로 저장
# - value가 숫자면 int 또는 float으로 변환, 문자열이면 따옴표 제거
# - FileNotFoundError 예외 처리로 파일 없을 때 경고 출력
# - JSON 파일을 루프마다 새로 읽기 때문에 파일 수정 후 저장 시 다음 사이클에 즉시 반영
def parse_json_file(filepath):
    """flat JSON 파일을 직접 파싱한다."""
    result = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 중괄호({}) 제거 후 줄 단위로 분리
        content = content.strip().strip("{}")
        lines = content.split("\n")

        for line in lines:
            # 앞뒤 공백 제거, 줄 끝 쉼표 제거
            line = line.strip().rstrip(",")
            if not line:
                continue

            # 콜론(:) 위치를 기준으로 키와 값을 분리
            colon_idx = line.index(":")
            key = line[:colon_idx].strip().strip('"')
            value = line[colon_idx + 1:].strip()

            # 소수점 포함 여부로 int / float 구분, 실패 시 문자열로 처리
            try:
                result[key] = float(value) if "." in value else int(value)
            except ValueError:
                result[key] = value.strip('"')

    except FileNotFoundError:
        print(f"[경고] '{filepath}' 파일을 찾을 수 없습니다.")

    return result


# JSON 형식 출력 함수)
# -> 파이썬 데이터를 JSON처럼 예쁘게 출력
# 문제 정의
# - 제약사항 : json 모듈 사용 불가
# - 수행과제에서 env_values를 JSON 형태로 출력해야 함
#
# 기술 구현
# - dict를 받아 JSON 포맷 문자열로 직접 변환
# - indent 파라미터로 들여쓰기 칸 수 조절 가능 (기본 4칸)
# 파이썬 None  →  JSON null       (규칙이 달라서 변환 필요)
# 파이썬 True  →  JSON true       (대소문자가 달라서 변환 필요)
# 숫자         →  그대로
# 마지막 항목  →  쉼표 없음       (JSON 표준 규칙)
def dict_to_json_str(data, indent=4):
    """dict를 JSON 형식 문자열로 변환한다."""
    lines = ["{"]
    items = list(data.items())

    for i, (key, value) in enumerate(items):
        # 마지막 항목이 아니면 쉼표 추가
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


# DummySensor 클래스 정의
class DummySensor:
    """JSON 파일에서 센서 데이터를 읽어오는 더미 센서 클래스."""

    # 수행과제 : 센서의 값을 가져오는 메소드
    def get_env_data(self):
        """JSON 파일을 직접 파싱해 환경 데이터를 반환한다."""
        return parse_json_file(SENSOR_DATA_FILE)


# 화성 기지의 환경 데이터를 수집하고 출력하는 미션 컴퓨터 클래스
class MissionComputer:
    """화성 기지 환경 데이터를 수집하고 출력하는 미션 컴퓨터 클래스."""

    def __init__(self):
        # 수행과제 : 화성 기지 환경값을 저장하는 딕셔너리 속성 (env_values)
        # 초기값은 None 
        self.env_values = {
            "mars_base_internal_temperature": None,   # 화성 기지 내부 온도
            "mars_base_external_temperature": None,   # 화성 기지 외부 온도
            "mars_base_internal_humidity": None,      # 화성 기지 내부 습도
            "mars_base_external_illuminance": None,   # 화성 기지 외부 광량
            "mars_base_internal_co2": None,           # 화성 기지 내부 이산화탄소 농도
            "mars_base_internal_oxygen": None,        # 화성 기지 내부 산소 농도
        }

        # 인스턴스 만들기
        self.ds = DummySensor()

        # -------------------------------------------------------
        # 보너스 과제 : 5분 평균 계산을 위한 누적 데이터 초기화
        # -------------------------------------------------------
        # 문제 정의
        # - 5분에 한 번씩 각 환경값의 5분 평균을 별도로 출력해야 함
        #
        # 기술 구현
        # - _sum_values : 각 키의 누적합 저장 (평균 계산용)
        # - _count : 누적 횟수 저장 (평균 계산용)
        # - _last_avg_time : 마지막 평균 출력 시각 저장 (time.time() 기준)
        # - 5초 루프마다 누적 → 300초 경과 시 평균 출력 → 초기화 반복
        self._sum_values = {key: 0.0 for key in self.env_values}
        self._count = 0
        self._last_avg_time = None

    # 센서 데이터를 env_values에 반영하는 내부 메소드
    # 센서가 보내온 데이터 업데이트 하는 메소드
    def _update_env_values(self, sensor_data):
        """센서 데이터를 env_values와 누적합에 반영한다."""
        for key in self.env_values:
            if key in sensor_data and sensor_data[key] is not None:
                self.env_values[key] = sensor_data[key]

                # 평균 계산을 위해 누적합에 더함
                self._sum_values[key] += sensor_data[key]

        # 평균 계산을 위해 누적 횟수 증가
        self._count += 1

    # -------------------------------------------------------
    # 보너스 과제 : 5분 평균 출력 메소드
    # -------------------------------------------------------
    # 5분에 한 번씩 각 환경값에 대한 5분 평균값을 별도로 출력
    #
    # 기술 구현
    # - _sum_values의 각 값을 _count로 나눠 평균 계산
    # - round()로 소수점 2자리까지 반올림
    # - dict_to_json_str()으로 JSON 형태로 출력
    # - 출력 후 _reset_average()로 누적 데이터 초기화
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

    # 평균 출력 후 호출하여 다음 5분 구간 누적을 새로 시작
    def _reset_average(self):
        """평균 계산용 누적 데이터를 초기화한다."""
        self._sum_values = {key: 0.0 for key in self.env_values}
        self._count = 0


    # 세 가지 수행과제 기능을 포함
    # 1. 센서의 값을 가져와서 env_values에 담기
    # 2. env_values를 JSON 형태로 출력
    # 3. 위 두 동작을 5초에 한 번씩 반복
    #
    # 보너스 과제 두 가지도 이 메소드에서 처리
    # 1. 특정 키(q) 입력 시 반복 출력 정지 → "System stopped...." 출력
    # 2. 5분마다 각 환경값의 평균 출력
    def get_sensor_data(self):
        """센서 데이터를 읽어 출력하고, 5분마다 평균을 출력한다."""
        print("미션 컴퓨터 가동 시작.")
        print("다음 사이클로 넘어가려면 Enter, 종료하려면 q 입력\n")

        # 보너스 과제 : 5분 타이머 시작 기준 시각 저장
        self._last_avg_time = time.time()

        try:
            while True:
                # 센서에서 데이터를 읽어 env_values에 저장
                sensor_data = self.ds.get_env_data()
                self._update_env_values(sensor_data)

                # env_values를 JSON 형태로 출력
                print(dict_to_json_str(self.env_values))
                print("-" * 40)

                # -------------------------------------------------------
                # 5분 평균 출력 체크
                # -------------------------------------------------------
                # 기술 구현
                # - time.time()으로 현재 시각을 구해 마지막 평균 출력 시각과 차이를 계산
                # - 차이가 AVERAGE_INTERVAL(300초) 이상이면 평균 출력 후 타이머 리셋
                # - threading 없이 단일 루프 안에서 time.time() 비교만으로 구현
                if time.time() - self._last_avg_time >= AVERAGE_INTERVAL:
                    self._print_average()
                    self._reset_average()
                    self._last_avg_time = time.time()

                # -------------------------------------------------------
                # 보너스 과제 : 특정 키 입력 시 정지
                # -------------------------------------------------------
                # - 특정 키를 입력하면 반복 출력을 멈추고 "System stopped...." 출력


                # - threading, select 등 추가 모듈 없이 input()만으로 구현
                # - sleep(5) 앞에 input()을 배치하여 블로킹 특성을 역으로 활용
                # - 루프마다 사용자 입력을 기다리는 구조로 자연스럽게 키 감지
                # - q 입력 시 break로 루프 탈출 → 종료 메시지 출력
                # - 그 외 Enter 입력 시 sleep(5) 후 다음 사이클 진행
                user_input = input("▶ ").strip().lower()

                if user_input == "q":
                    print("사이클에서 벗어납니다...")
                    print("System stopped....")
                    break

                # 5초 대기 후 반복
                print(f"{READ_INTERVAL}초 후 데이터를 갱신합니다...\n")
                time.sleep(READ_INTERVAL)

        # Ctrl+C 강제 종료 시에도 "System stopped...." 출력
        except KeyboardInterrupt:
            print("\n사이클에서 벗어납니다...")
            print("System stopped....")


RunComputer = MissionComputer()

RunComputer.get_sensor_data()