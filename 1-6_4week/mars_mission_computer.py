import random
import datetime


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0,
        }

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 1)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 1)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 1)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 1)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 2)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 1)

    # -----------------------------------------------
    # 보너스 과제
    # 날짜, 시간, 화성기지 내부온도 등을 로그로 남겨
    # 파일로 저장하기 (get_env() 에 추가하기)
    # -----------------------------------------------

    def get_env(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log = (
            f'{now}, '
            f'{self.env_values["mars_base_internal_temperature"]}, '
            f'{self.env_values["mars_base_external_temperature"]}, '
            f'{self.env_values["mars_base_internal_humidity"]}, '
            f'{self.env_values["mars_base_external_illuminance"]}, '
            f'{self.env_values["mars_base_internal_co2"]}, '
            f'{self.env_values["mars_base_internal_oxygen"]}\n'
        )
        header = (
            'datetime, '
            'mars_base_internal_temperature, '
            'mars_base_external_temperature, '
            'mars_base_internal_humidity, '
            'mars_base_external_illuminance, '
            'mars_base_internal_co2, '
            'mars_base_internal_oxygen\n'
        )

        for filename in ['1-6_4week/mars_mission_log.log', '1-6_4week/mars_mission_log.csv']:
            # 파일이 없으면 헤더 먼저 쓰고, 있으면 바로 로그 추가
            with open(filename, 'a') as f:
                if f.tell() == 0:
                    f.write(header)
                f.write(log)

        return self.env_values


ds = DummySensor()
# ds.set_env()
# 이 문장 안 할 시 0.0만 나옴
# set_env()로 센서 값을 설정한 뒤 get_env()로 값을 확인한다
ds.set_env()
print(ds.get_env())