# javis.py
# 화성 기지 음성 일지 녹음 시스템 (JAVIS - Just A Voice Interface System)
# 한송희 박사의 화성 생활 기록을 음성으로 남기기 위한 프로그램
#
# [사용 라이브러리 요약]
#   - os       : 기본 내장 라이브러리 - 파일/디렉토리 경로 관리
#   - wave     : 기본 내장 라이브러리 - WAV 오디오 파일 포맷 저장
#   - datetime : 기본 내장 라이브러리 - 날짜/시간 기반 파일명 생성
#   - pyaudio  : ★ 외부 라이브러리 (음성 녹음 부분에만 허용) - 마이크 접근 및 스트림 처리

import os        # 파일·디렉토리 존재 확인, 경로 합성, 목록 조회에 사용
import wave      # 녹음 데이터를 WAV 포맷으로 저장하기 위해 사용 (별도 인코딩 불필요)
import datetime  # 현재 날짜·시간으로 파일명 생성 및 날짜 비교에 사용

# ★★★ 외부 라이브러리 - 음성 녹음 허용 범위 ★★★
# pyaudio: PortAudio 라이브러리의 파이썬 바인딩
#   - 크로스 플랫폼(Windows/macOS/Linux) 마이크 접근을 단일 API로 제공
#   - 스트리밍 방식으로 실시간 오디오 캡처 가능
#   - pip install pyaudio 로 설치
import pyaudio


# ──────────────────────────────────────────────────────────────
# 녹음 설정 상수 (PEP 8: 모듈 레벨 상수는 대문자 + 언더바)
# ──────────────────────────────────────────────────────────────

# CHUNK: 한 번에 읽을 오디오 프레임(샘플) 수
#   - 1024는 CPU 부하와 버퍼 지연 사이의 표준적인 균형점
#   - 너무 작으면 CPU 과부하, 너무 크면 지연(latency) 발생
CHUNK = 1024

# FORMAT: 각 샘플의 데이터 타입
#   - paInt16: 16비트 부호 정수 PCM (표준 WAV 품질, 범용 호환성 우수)
#   - 24/32비트 대비 파일 크기가 작고 음성 녹음에 충분한 품질
FORMAT = pyaudio.paInt16

# CHANNELS: 오디오 채널 수
#   - 1 = 모노: 음성 일지 목적이므로 스테레오(2) 불필요, 용량 절약
CHANNELS = 1

# RATE: 샘플링 레이트 (초당 샘플 수, Hz)
#   - 44100 Hz = CD 표준 품질
#   - 나이퀴스트 정리에 의해 22050 Hz까지의 소리를 왜곡 없이 기록 가능
RATE = 44100

# RECORDS_DIR: 녹음 파일이 저장될 폴더 이름 (실행 경로 기준 하위 폴더)
RECORDS_DIR = 'records'

# DEFAULT_DURATION: 기본 녹음 시간 (초)
DEFAULT_DURATION = 5


# ══════════════════════════════════════════════════════════════
# 클래스 정의
# ══════════════════════════════════════════════════════════════

class JavisRecorder:
    """화성 기지 음성 일지 녹음 및 관리 클래스.

    CapWords(PascalCase) 방식 적용:
      각 단어의 첫 글자를 대문자로 작성 (PEP 8 클래스 명명 규칙).

    주요 기능:
      - 시스템 마이크 인식 및 목록 출력
      - 오디오 녹음 후 날짜/시간 기반 파일명으로 WAV 저장
      - 특정 날짜 범위의 녹음 파일 조회 (보너스 과제)
    """

    def __init__(self):
        """객체 초기화 메서드.

        __init__: 인스턴스 생성 시 자동으로 호출됨.
        프로그램 시작 시점에 저장 폴더를 미리 생성해 둠.
        """
        # 인스턴스 생성 즉시 저장 폴더 존재 여부 확인 및 생성
        self._ensure_records_dir()

    def _ensure_records_dir(self):
        """records 폴더가 없으면 자동 생성하는 내부 메서드.

        _접두사: PEP 8 관례상 외부에서 직접 호출하지 않는 내부 메서드 표시.
        os.makedirs 선택 이유:
          - os.mkdir와 달리 중간 경로가 없어도 한 번에 생성 가능
          - exist_ok=True: 폴더가 이미 있어도 예외를 발생시키지 않음
            → 매 실행마다 안전하게 호출 가능
        """
        # ★ os.makedirs: 경로 전체를 한 번에 생성, exist_ok로 중복 오류 방지
        os.makedirs(RECORDS_DIR, exist_ok=True)

    def _generate_filename(self):
        """현재 날짜와 시간으로 저장 파일 경로를 생성하는 내부 메서드.

        파일명 형식: '년월일-시간분초.wav' (예: 20240521-143022.wav)

        datetime.datetime.now() 선택 이유:
          - 로컬 시스템 시각 사용 → 화성 현지 시간 기록에 적합
          - UTC 대신 로컬 시각: 일지 파일 정렬 시 직관적

        strftime() 선택 이유:
          - 날짜/시간 → 문자열 변환을 포맷 지정자로 정밀하게 제어 가능
          - %Y%m%d: 4자리 연도 + 2자리 월 + 2자리 일 → 사전식 정렬 = 날짜순 정렬
        """
        # ★ datetime.now(): 현재 로컬 시각 객체 생성
        now = datetime.datetime.now()

        # strftime 포맷 설명:
        #   %Y = 4자리 연도 (예: 2024)
        #   %m = 2자리 월   (예: 05)
        #   %d = 2자리 일   (예: 21)
        #   %H = 24시간제 시 (예: 14)
        #   %M = 분         (예: 30)
        #   %S = 초         (예: 22)
        filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'

        # ★ os.path.join: OS별 경로 구분자(\, /)를 자동 처리하여 안전한 경로 생성
        return os.path.join(RECORDS_DIR, filename)

    def list_microphones(self):
        """시스템에 연결된 마이크(입력 장치) 목록을 출력하는 메서드.

        pyaudio.PyAudio() 선택 이유:
          - 운영체제와 무관하게 동일한 API로 오디오 장치 열거 가능
          - get_device_info_by_index()로 장치별 입출력 채널 수 등 상세 정보 확인

        maxInputChannels > 0 필터링 이유:
          - 스피커 등 출력 전용 장치는 maxInputChannels == 0
          - 마이크(입력 가능 장치)만 골라내기 위한 조건
        """
        # ★ pyaudio.PyAudio(): 오디오 시스템 접근의 진입점 인스턴스 생성
        audio = pyaudio.PyAudio()

        print('=== 인식된 마이크 목록 ===')

        # get_device_count(): 시스템 전체 오디오 장치 수 반환 → range로 순회
        for i in range(audio.get_device_count()):
            # ★ get_device_info_by_index(): 인덱스로 장치 정보 딕셔너리 반환
            device_info = audio.get_device_info_by_index(i)

            # maxInputChannels > 0: 입력(마이크) 기능이 있는 장치만 출력
            if device_info['maxInputChannels'] > 0:
                print(f"[{i}] {device_info['name']}")

        # ★ terminate(): PyAudio 인스턴스가 점유한 PortAudio 리소스 해제
        #   → 사용 후 반드시 호출해야 메모리 누수 및 장치 잠금 방지
        audio.terminate()

    def record_audio(self, duration=DEFAULT_DURATION):
        """마이크로 오디오를 녹음하고 WAV 파일로 저장하는 핵심 메서드.

        Args:
            duration (int): 녹음 시간 (초 단위, 기본값 DEFAULT_DURATION=5초)

        Returns:
            str: 저장된 파일 경로 문자열

        알고리즘 설명:
          1. 파일 경로 사전 생성 (날짜/시간 기반)
          2. PyAudio 스트림을 열어 CHUNK 단위로 데이터를 읽어 리스트에 누적
          3. 스트림 종료 후 누적 데이터를 wave 모듈로 WAV 파일에 기록

        스트리밍 방식 선택 이유:
          - 전체 녹음 데이터를 메모리에 한 번에 올리지 않고 청크 단위로 처리
          - 긴 녹음 시에도 메모리 사용량이 일정하게 유지됨
        """
        # 녹음 시작 전에 파일 경로 결정 (시작 시각 기준)
        filepath = self._generate_filename()

        # ★ PyAudio 인스턴스 생성
        audio = pyaudio.PyAudio()

        # get_sample_size(): FORMAT(paInt16)에 해당하는 바이트 크기(2바이트) 반환
        # ★ terminate() 전에 미리 저장해 두는 이유:
        #   terminate() 호출 후에는 audio 객체를 사용할 수 없으므로 선제 저장
        sample_size = audio.get_sample_size(FORMAT)

        print('녹음을 시작합니다...')

        # ★ audio.open(): 오디오 입력 스트림 열기
        #   format           : 샘플 데이터 타입 (16비트 PCM)
        #   channels         : 채널 수 (1=모노)
        #   rate             : 샘플링 레이트 (44100 Hz)
        #   input=True       : 입력(마이크) 스트림 활성화 (False면 출력용)
        #   frames_per_buffer: 한 번에 처리할 프레임 수 (= CHUNK)
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        # 청크 단위로 읽어온 바이트 데이터를 누적할 리스트
        frames = []

        # 반복 횟수 계산 알고리즘:
        #   RATE / CHUNK = 초당 읽어야 할 청크 수
        #   × duration   = 전체 녹음 시간 동안 필요한 총 청크 수
        #   int()         : range()는 정수만 허용하므로 정수 변환 필요
        total_chunks = int(RATE / CHUNK * duration)

        for _ in range(total_chunks):
            # ★ stream.read(): 마이크에서 CHUNK 프레임만큼 바이트 데이터 읽기
            #   exception_on_overflow=False 옵션 없이 기본 호출
            #   → 시스템 성능에 따라 overflow 발생 시 예외 처리 가능
            data = stream.read(CHUNK)
            frames.append(data)  # 바이트 데이터를 리스트에 순서대로 누적

        print('녹음이 완료되었습니다.')

        # ★ 스트림 정리 (순서 중요: stop → close → terminate)
        stream.stop_stream()  # 스트림 데이터 흐름 중지
        stream.close()        # 스트림 객체 닫기 (파일 핸들 해제)
        audio.terminate()     # PyAudio 인스턴스 및 PortAudio 리소스 해제

        # ★ WAV 파일 저장
        # wave.open() 선택 이유:
        #   - 파이썬 기본 내장 라이브러리로 별도 설치 불필요
        #   - WAV 헤더(채널 수, 샘플 크기, 레이트)를 자동으로 작성해 줌
        #   - 'wb' 모드: 바이너리 쓰기 (오디오 데이터는 이진 데이터)
        # with 문 사용 이유: 블록 종료 시 wf.close() 자동 호출 → 리소스 안전 해제
        with wave.open(filepath, 'wb') as wf:
            # ★ WAV 헤더 설정 (파일 재생 시 올바른 오디오 해석을 위해 필수)
            wf.setnchannels(CHANNELS)    # 채널 수 기록 (1=모노)
            wf.setsampwidth(sample_size) # 샘플당 바이트 수 기록 (paInt16 = 2바이트)
            wf.setframerate(RATE)        # 샘플링 레이트 기록 (44100 Hz)

            # ★ b''.join(frames): 바이트 리스트 → 하나의 연속된 바이트 객체로 병합
            #   ''.join()의 바이트 버전 → str.join()보다 메모리 효율적
            wf.writeframes(b''.join(frames))

        print(f'파일이 저장되었습니다: {filepath}')
        return filepath

    def list_records_by_date_range(self, start_date_str, end_date_str):
        """특정 날짜 범위에 해당하는 녹음 파일 목록을 반환하는 보너스 과제 메서드.

        Args:
            start_date_str (str): 시작 날짜 문자열 ('YYYYMMDD' 형식, 예: '20240101')
            end_date_str   (str): 종료 날짜 문자열 ('YYYYMMDD' 형식, 예: '20241231')

        Returns:
            list[str]: 날짜 범위에 해당하는 파일명 리스트 (오름차순 정렬)

        알고리즘 설명:
          1. 입력 문자열을 datetime 객체로 변환 (형식 검증 포함)
          2. records 폴더의 파일 목록을 순회
          3. 파일명 앞 8자리(날짜 부분)를 추출해 범위 내 파일만 필터링
          4. 정렬 후 반환 (파일명 사전순 = 날짜/시간 오름차순)

        os.listdir() 선택 이유:
          - 기본 내장 함수로 외부 라이브러리 불필요
          - 폴더 내 파일명 목록을 리스트로 바로 반환
        """
        # ★ strptime(): 문자열 → datetime 객체 변환 (형식 불일치 시 ValueError 발생)
        #   형식 지정자 '%Y%m%d': 8자리 숫자 날짜 파싱
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y%m%d')
            end_date = datetime.datetime.strptime(end_date_str, '%Y%m%d')
        except ValueError:
            # 잘못된 날짜 형식 입력 시 사용자에게 안내 후 빈 리스트 반환
            print('날짜 형식이 올바르지 않습니다. YYYYMMDD 형식으로 입력하세요.')
            return []

        # 시작일이 종료일보다 늦은 논리적 오류 방지
        if start_date > end_date:
            print('시작 날짜가 종료 날짜보다 늦습니다. 날짜를 확인하세요.')
            return []

        # records 폴더 존재 여부 확인
        if not os.path.exists(RECORDS_DIR):
            print('records 폴더가 없습니다. 녹음 파일이 아직 없습니다.')
            return []

        # 날짜 범위에 해당하는 파일명을 담을 리스트
        matched_files = []

        # ★ os.listdir(): 폴더 내 파일·디렉토리 이름을 리스트로 반환
        #   glob 미사용 이유: 기본 내장 라이브러리만 사용하는 제약 준수
        for filename in os.listdir(RECORDS_DIR):
            # .wav 확장자 파일만 처리 (다른 형식 파일 무시)
            if not filename.endswith('.wav'):
                continue

            # 파일명 구조: 'YYYYMMDD-HHMMSS.wav'
            # split('-')[0]: 하이픈을 기준으로 분리 후 첫 번째 요소(날짜 8자리) 추출
            parts = filename.split('-')

            # 파일명이 예상 구조와 다를 경우(하이픈 없음 등) 건너뜀
            if len(parts) < 2:
                continue

            date_part = parts[0]  # 'YYYYMMDD' 문자열 추출

            try:
                # 파일명의 날짜 부분을 datetime 객체로 변환하여 비교 가능하게 만듦
                file_date = datetime.datetime.strptime(date_part, '%Y%m%d')
            except ValueError:
                # 날짜 형식이 맞지 않는 파일명은 조용히 건너뜀
                continue

            # ★ 범위 포함 비교: start_date ≤ file_date ≤ end_date
            #   datetime 객체는 비교 연산자(<=, >=)를 직접 지원
            if start_date <= file_date <= end_date:
                matched_files.append(filename)

        # ★ sorted(): 파일명 기준 사전식 오름차순 정렬
        #   파일명이 'YYYYMMDD-HHMMSS.wav' 형식이므로 사전순 = 날짜/시간 오름차순
        return sorted(matched_files)

    def show_records_by_date_range(self, start_date_str, end_date_str):
        """날짜 범위 조회 결과를 보기 좋게 출력하는 메서드.

        list_records_by_date_range()와 출력 책임을 분리:
          - 데이터 조회 로직(list_records_by_date_range)과 출력 로직을 분리
          - 단일 책임 원칙(SRP) 준수
        """
        print(f'\n=== {start_date_str} ~ {end_date_str} 녹음 파일 목록 ===')

        # 내부 조회 메서드 호출하여 파일 목록 획득
        files = self.list_records_by_date_range(start_date_str, end_date_str)

        if not files:
            # 결과가 없을 경우 안내 메시지 출력
            print('해당 날짜 범위에 녹음 파일이 없습니다.')
        else:
            # enumerate() 선택 이유: 인덱스와 값을 동시에 순회, start=1로 1번부터 출력
            for i, filename in enumerate(files, start=1):
                print(f'{i}. {filename}')
            # 총 파일 수 요약 출력
            print(f'\n총 {len(files)}개의 파일이 있습니다.')


# ══════════════════════════════════════════════════════════════
# 독립 함수 정의 (PEP 8: snake_case 사용)
# ══════════════════════════════════════════════════════════════

def show_menu():
    """메인 메뉴 선택지를 출력하는 함수.

    함수명 show_menu: 소문자 + 언더바 방식(snake_case) 적용 (PEP 8 함수 명명 규칙).
    메뉴 출력과 입력 처리를 분리하여 가독성 향상.
    """
    print('\n=== JAVIS - 화성 기지 음성 일지 시스템 ===')
    print('1. 마이크 목록 확인')
    print('2. 음성 녹음')
    print('3. 날짜 범위로 녹음 파일 조회 (보너스)')
    print('0. 종료')
    print('==========================================')


def get_user_choice():
    """메뉴 선택 번호를 입력받아 반환하는 함수.

    Returns:
        str: 공백이 제거된 사용자 입력 문자열

    input() 선택 이유: 표준 입력으로 사용자 입력을 받는 파이썬 기본 내장 함수.
    strip() 사용 이유: 앞뒤 공백·개행문자 제거 → 의도치 않은 입력 오류 방지.
    """
    # ★ strip(): 사용자가 실수로 공백을 입력해도 정상 처리
    return input('메뉴를 선택하세요: ').strip()


def get_duration_input():
    """녹음 시간(초)을 사용자에게 입력받는 함수.

    Returns:
        int: 유효한 녹음 시간 (초 단위)

    입력값 검증 알고리즘:
      - 빈 입력 → 기본값(DEFAULT_DURATION) 사용
      - 양의 정수 → 그 값 사용
      - 그 외 → 안내 후 재입력 요청
    """
    while True:
        # 기본값 안내를 포함한 프롬프트 메시지
        raw = input(
            f'녹음 시간을 입력하세요 (기본값 {DEFAULT_DURATION}초, '
            f'Enter로 기본값 사용): '
        ).strip()

        # 빈 입력: 기본값 반환
        if raw == '':
            return DEFAULT_DURATION

        # 숫자 변환 시도
        try:
            # int(): 문자열 → 정수 변환 내장 함수
            duration = int(raw)
            if duration > 0:
                return duration
            # 0 이하 입력 방지
            print('1초 이상의 숫자를 입력하세요.')
        except ValueError:
            # 정수로 변환 불가능한 입력 처리
            print('올바른 숫자를 입력하세요.')


def get_date_range_input():
    """시작 날짜와 종료 날짜를 사용자에게 입력받는 함수.

    Returns:
        tuple[str, str]: (시작 날짜 문자열, 종료 날짜 문자열) - 'YYYYMMDD' 형식

    별도 함수로 분리한 이유:
      - main() 함수의 복잡도를 낮춤 (단일 책임 원칙)
      - 날짜 입력 로직 재사용 가능
    """
    start_str = input('시작 날짜를 입력하세요 (예: 20240101): ').strip()
    end_str = input('종료 날짜를 입력하세요 (예: 20241231): ').strip()
    return start_str, end_str


def main():
    """프로그램 진입점 메인 함수.

    JavisRecorder 인스턴스를 생성하고 사용자 메뉴 루프를 실행.

    while True 루프 선택 이유:
      - 사용자가 '0'(종료)을 선택할 때까지 무한 반복
      - break 문으로 명시적 종료 → 루프 의도가 코드에 드러남

    구조:
      1. JavisRecorder 인스턴스 생성 (records 폴더 자동 생성 포함)
      2. 메뉴 출력 → 입력 → 기능 실행 반복
    """
    # ★ JavisRecorder 인스턴스 생성: __init__에서 records 폴더 자동 생성
    recorder = JavisRecorder()

    # 메인 루프: 종료 선택 전까지 반복
    while True:
        show_menu()
        choice = get_user_choice()

        if choice == '1':
            # 마이크 목록 출력
            recorder.list_microphones()

        elif choice == '2':
            # 녹음 시간 입력받은 후 녹음 시작
            duration = get_duration_input()
            recorder.record_audio(duration=duration)

        elif choice == '3':
            # 보너스 과제: 날짜 범위 입력받아 파일 목록 조회
            start_str, end_str = get_date_range_input()
            recorder.show_records_by_date_range(start_str, end_str)

        elif choice == '0':
            # 종료 선택 시 안내 메시지 후 루프 탈출
            print('JAVIS를 종료합니다. 화성에서의 기록을 마칩니다.')
            break

        else:
            # 잘못된 입력 처리: 루프 계속 유지
            print('올바른 메뉴 번호를 선택하세요 (0~3).')


# ══════════════════════════════════════════════════════════════
# ★★★ 스크립트 진입점 가드 (PEP 8 필수 관례) ★★★
#
# if __name__ == '__main__': 필요한 이유:
#   - 이 파일을 직접 실행(python javis.py)할 때만 main() 호출
#   - 다른 파일에서 import할 경우 main()이 자동 실행되지 않음
#     → 모듈 재사용성 보장
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    main()