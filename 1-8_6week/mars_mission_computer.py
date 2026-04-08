# 문제 7에서 완성한 MissionComputer 클래스에 있던 부분
import time

# 이번 문제에 쓸 라이브러리
import platform
import os

# 파일 경로 설정을 위한 기본 로직 (모듈 없이 처리)
script_dir = __file__.replace('\\', '/').rsplit('/', 1)[0]
SENSOR_DATA_FILE = script_dir + '/sensor_data.json'  # 5주차 시스템 정보 저장용
CONFIG_DATA_FILE = script_dir + '/config_data.json'  # 시스템 사양 정보 저장용
SETTING_FILE = script_dir + '/setting.txt'        # 보너스 과제: 출력 항목 설정용

READ_INTERVAL = 5
AVERAGE_INTERVAL = 300


# 외부 데이터를 읽어오는 파서(지난 주 코드 활용)
# import json 없이 데이터를 처리하는 알고리즘
# -> 그냥 노다가 알고리즘...
def parse_json_file(filepath):
    '''JSON 파일을 직접 파싱하여 딕셔너리로 반환한다.'''
    result = {}
    if not os.path.exists(filepath):
        return result
    try:
        # json파일을 텍스트로 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip().strip('{}')

            # 줄바꿈으로 데이터를 한 줄씩 쪼개기
            lines = content.split('\n')
            for line in lines:
                line = line.strip().rstrip(',')
                if not line or ':' not in line:
                    continue

                # 콜론( : )을 기준으로 키와 값을 분리하는 알고리즘
                colon_idx = line.index(':')
                key = line[:colon_idx].strip().strip('"').strip("'")
                value = line[colon_idx + 1:].strip().strip('"').strip("'")
                
                # 타입 변환 (숫자면 숫자로, 문자열이면 문자열로 저장)
                try:
                    result[key] = float(value) if '.' in value else int(value)
                except ValueError:
                    result[key] = value
    except Exception:
        pass
    return result

# 결과물을 json 형태로 만드는 수동 포맷터(지난 주 코드 확장버전)
def dict_to_json_str(data, indent=4):
    '''dict를 JSON 형식 문자열로 직접 변환한다.'''
    lines = ['{'] # -> 이 부분은 json의 시작인 중괄호를 리스트에 먼저 넣는 코드

    # json 파일 안의 데이터들을 추출
    items = list(data.items())


    # 데이터를 하나씩 꺼내며 JSON 규격에 맞춰서 문자열을 만듬
    # 전체 데이터 갯수에서 1을 뺀 값보다 작을 때만 ,를 붙이고
    # 마지막 항목에는 ''를 붙인다
    for i, (key, value) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        pad = ' ' * indent

        # 파이썬 데이터 타입을 JSON 규격으로 치환

        # 파이썬에서 None값을 Json 형태로는 null로 치환하는 역할
        if value is None:
            lines.append(f'{pad}"{key}": null{comma}')
        # 파이썬에서 bool값을 Json 형태로는 true, false로 치환하는 역할
        elif isinstance(value, bool):
            lines.append(f'{pad}"{key}": {str(value).lower()}{comma}')
        # 파이썬에서 int값이나 float값을 그대로 출력 (JSON에서는 숫자를 따옴표로 감싸지 않음)
        elif isinstance(value, (int, float)):
            lines.append(f'{pad}"{key}": {value}{comma}')
        # 파이썬에서 문자열값을 ""안에 들어가게 만들고 치환하는 역할
        else:
            lines.append(f'{pad}"{key}": "{value}"{comma}')
    lines.append('}')


    # 리스트 요소들을 커다란 문자열로 합쳐주는 join 메소드 사용
    # 합치기 전의 상태 ['{', '    "os": "Windows"', '}']
    # 합친 후의 상태 { 
    #                "os": "Windows"   -> 훨씬 더 깔끔
    #               }
    return '\n'.join(lines)


class DummySensor:
    '''JSON 파일에서 센서 데이터를 읽어오는 더미 센서 클래스.'''
    def get_env_data(self):
        return parse_json_file(SENSOR_DATA_FILE)



class MissionComputer:
    '''화성 기지 환경 및 시스템 정보를 관리하는 미션 컴퓨터 클래스.'''

    def __init__(self):
        # 환경 데이터 속성
        self.env_values = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None,
        }
        self.ds = DummySensor()
        self._sum_values = {key: 0.0 for key in self.env_values}
        self._count = 0
        self._last_avg_time = time.time()

    def _get_active_settings(self):
        '''보너스 과제: setting.txt에서 출력할 항목 리스트를 가져온다.'''
        
        # 만약 setting.txt.가 없다면 빈 리스트 반환
        if not os.path.exists(SETTING_FILE):
            return []
        
        with open(SETTING_FILE, 'r', encoding='utf-8') as f:
            # 파일의 내용을 한 줄씩 가져오고 불필요한 공백이나 줄바꿈 문자를 깔끔하게 깎아내기
            return [line.strip() for line in f.readlines() if line.strip()]

    # 실제 json 데이터들 중에서 중요한 데이터를 뽑아오는 메소드
    # 안전장치 알고리즘 -> 파일이 비어있거나 설정이 없으면 일단 다 보여줌
    def _filter_output(self, data_dict):
        '''설정 파일에 따라 출력 데이터를 필터링하는 알고리즘.'''
        settings = self._get_active_settings()
        if not settings:
            return data_dict
        return {k: v for k, v in data_dict.items() if k in settings}

    # 시스템 정보 조회 메소드
    def get_mission_computer_info(self):
        '''컴퓨터의 시스템 정보를 가져와 JSON 형식으로 출력한다.'''
        info = {}
        try:
            # platform 라이브러리로 OS 이름과 버전 획득
            info['운영체계'] = platform.system()
            info['운영체계 버전'] = platform.version()
            info['CPU의 타입'] = platform.processor()

            # os 라이브러리로 CPU 코어 수 확인
            info['CPU의 코어 수'] = os.cpu_count()
            
            # [중요] 메모리 정보는 파이썬 파일 안에서 만들지 말고 JSON에서 가져오기
            config = parse_json_file(CONFIG_DATA_FILE)
            info['메모리의 크기'] = config.get('memory_size', '16GB')
        
        
        except Exception as e:
            print(f'[오류] 시스템 정보 획득 실패: {e}')

        
        # ========================================================================
        # 보너스 과제
        # _filter_output을 이용해 setting 텍스트 파일에 적힌 항목만 남김
        # ========================================================================
        filtered_info = self._filter_output(info)
        print('\n--- [Mission Computer Info] ---')
        print(dict_to_json_str(filtered_info))
        return filtered_info


    # 실시간 부하 조회 메소드
    def get_mission_computer_load(self):
        '''컴퓨터의 부하 정보를 가져와 JSON 형식으로 출력한다.'''
        load = {}
        try:
            print('\n[부하 측정 센서 가동 중...]')

            # 라이브러리 대신 input() 함수로 실시간 값을 입력받는 알고리즘
            # psutil 라는 라이브러리를 이용하면 실시간으로 CPU나 메모리의 사용량을 알 수 있으나
            # 제약사항으로 input으로 입력을 하는 알고리즘을 쓰게 됨
            cpu_val = input('현재 실시간 CPU 사용량을 입력하세요(예: 15): ')
            mem_val = input('현재 실시간 메모리 사용량을 입력하세요(예: 42): ')
            
            # 기본값으로 10과 25을 설정하고 단위를 부착
            load['CPU 실시간 사용량'] = (cpu_val if cpu_val else '10') + '%'
            load['메모리 실시간 사용량'] = (mem_val if mem_val else '25') + '%'
        except Exception as e:
            print(f'[오류] 부하 정보 측정 실패: {e}')


        # 위에서 만든 load 딕셔너리를 _filter_output 메소드로 보내
        # 데이터를 저장 및 가공
        filtered_load = self._filter_output(load)
        print('\n--- [Mission Computer Load] ---')
        print(dict_to_json_str(filtered_load))
        return filtered_load

    # 기존 환경 데이터 수집 메소드 (지난주 코드)
    def get_sensor_data(self):
        '''환경 데이터를 수집하고 루프를 돌며 출력한다.'''
        print('\n미션 컴퓨터 환경 감시 모드 가동.')
        try:
            # sensor_data.json으로부터 정보를 계속 가져옴
            while True:
                sensor_data = self.ds.get_env_data()
                self._update_env_values(sensor_data)
                print(dict_to_json_str(self.env_values))
                
                # q 입력 시 종료
                user_input = input('▶ [q: 종료 / Enter: 계속]: ').strip().lower()
                if user_input == 'q':
                    print('System stopped....')
                    break
                time.sleep(READ_INTERVAL)
        except KeyboardInterrupt:
            print('\nSystem stopped....')

    # 더미센서로 부터 얻은 데이터를 업데이트
    # self.env_values는 이전의 더미센서 클래스 데이터
    # sensor_data 변수가 업데이트 하면서 갱신된 데이터
    def _update_env_values(self, sensor_data):
        for key in self.env_values:
            if key in sensor_data:
                self.env_values[key] = sensor_data[key]


# 인스턴스화 및 실행부
if __name__ == '__main__':
    # MissionComputer 클래스를 runComputer 라는 이름으로 인스턴스화
    runComputer = MissionComputer()

    # 메소드 호출을 통해 시스템 및 부하 정보 출력
    runComputer.get_mission_computer_info()
    runComputer.get_mission_computer_load()
    
    # 지난 주의 코드 실행 메소드
    # runComputer.get_sensor_data()