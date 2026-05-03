"""
door_hacking.py

화성 기지 emergency storage 잠금 해제를 위한 zip 파일 브루트포스 암호 해독기.

암호 조건: 숫자(0-9) + 소문자 알파벳(a-z), 6자리, 특수문자 없음
           → 전체 경우의 수: 36^6 = 2,176,782,336 가지

알고리즘:
  [기본]  itertools.product로 모든 조합을 순서대로 생성하여 완전 탐색.
          ZipCrypto 헤더(12바이트)만 먼저 검사해 전체 압축 해제 횟수를 줄임.
  [보너스] 탐색 공간을 CPU 코어 수만큼 분할하여 multiprocessing으로 병렬 탐색.

제약사항 준수:
  - zipfile(zip 처리), 그 외 모두 Python 표준 라이브러리만 사용
  - 파일 처리 전 구간 예외처리 (FileNotFoundError, OSError 등)
  - 경고 없이 실행되도록 Python 3.14 변경된 예외(zlib.error, BadZipFile) 대응
  - PEP 8 스타일 가이드 준수
"""

# itertools: 6자리 모든 조합을 중첩 for문 없이 생성하기 위해 사용
# (product(charset, repeat=6) → 000000, 000001, ..., zzzzzz 순으로 자동 순회)
import itertools

# multiprocessing: GIL(전역 인터프리터 락) 때문에 threading으로는
# CPU 연산이 진짜 병렬화가 안 됨 → 별도 프로세스를 생성해 코어별 병렬 탐색
import multiprocessing

# os: 실행 위치와 무관하게 스크립트 파일 기준 절대경로를 계산하기 위해 사용
# (다른 컴퓨터, 다른 터미널 위치에서 실행해도 zip 파일을 항상 찾을 수 있음)
import os

# string: 문자셋을 하드코딩 없이 안전하게 정의
# string.digits      → '0123456789'
# string.ascii_lowercase → 'abcdefghijklmnopqrstuvwxyz'
import string

# struct: zip 로컬 파일 헤더를 직접 파싱하기 위해 사용
# (파일명 길이, 추가 필드 길이를 이진 데이터에서 읽어 암호화 헤더 위치 계산)
import struct

# time: 과제 요구사항인 시작 시간·반복 횟수·경과 시간 출력에 사용
import time

# zipfile: zip 파일 읽기 및 ZipCrypto 복호화기(_ZipDecrypter) 사용
# → 제약사항에서 "zip 파일 다루는 부분은 외부 라이브러리 사용 가능"으로 명시 허용
import zipfile

# zlib: Python 3.14에서 틀린 암호 시도 시 zlib.error가 추가로 발생하므로
# 명시적으로 import하여 예외 처리에 사용
import zlib

# ---------------------------------------------------------------------------
# 전역 상수
# ---------------------------------------------------------------------------

# os.path.abspath(__file__): 현재 스크립트의 절대경로
# os.path.dirname(...)     : 그 파일이 속한 폴더 경로
# → 터미널 위치, 컴퓨터가 달라져도 항상 스크립트 옆 파일을 가리킴
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ZIP_PATH = os.path.join(_BASE_DIR, 'emergency_storage_key.zip')
PASSWORD_FILE = os.path.join(_BASE_DIR, 'password.txt')

# 암호 조건: 숫자 10개 + 소문자 26개 = 36가지 문자
# string 모듈 사용으로 오타 없이 안전하게 정의
CHARSET = string.digits + string.ascii_lowercase  # '0123456789abcdefghijklmnopqrstuvwxyz'

PASSWORD_LENGTH = 6  # 암호 자릿수

# 진행 상황을 출력할 시도 횟수 간격
# 너무 잦으면 출력 자체가 속도를 늦추므로 50만 단위로 설정
LOG_INTERVAL = 500_000


# ---------------------------------------------------------------------------
# 내부 유틸리티: ZipCrypto 헤더 검사 (핵심 최적화)
# ---------------------------------------------------------------------------

def _check_password_fast(zf, zinfo, pwd_bytes):
    """
    ZipCrypto 암호화 헤더(12바이트)만 복호화하여 암호 일치 여부를 빠르게 확인한다.

    [왜 이 방법이 빠른가?]
      기존 방식: 암호 시도 → 파일 전체 압축 해제 → 성공/실패 판단  (느림)
      이 방식  : 암호 시도 → 헤더 12바이트만 복호화 → 1바이트 비교  (10~30배 빠름)

    [ZipCrypto 헤더 검사 원리]
      ZipCrypto 규격에 따라 암호화 헤더의 마지막 바이트(12번째)는
      반드시 해당 파일의 CRC-32 최상위 1바이트와 일치해야 한다.
      이 조건을 만족하지 않으면 틀린 암호이므로 즉시 skip할 수 있다.
      (256분의 1 확률로 오탐 발생 → 최종 확인 단계에서 걸러냄)

    [zip 로컬 헤더 구조 (ZIP 표준 규격)]
      오프셋 0  ~ 3  : 시그니처 (PK\x03\x04)
      오프셋 26 ~ 27 : 파일명 길이 (2바이트, little-endian)
      오프셋 28 ~ 29 : 추가 필드 길이 (2바이트, little-endian)
      오프셋 30 + 파일명 길이 + 추가 필드 길이: 실제 데이터 시작
      → 데이터 첫 12바이트가 ZipCrypto 암호화 헤더

    Args:
        zf (zipfile.ZipFile): 열린 ZipFile 객체.
        zinfo (zipfile.ZipInfo): 검사할 파일의 메타데이터.
        pwd_bytes (bytes): 시도할 암호 (bytes).

    Returns:
        bool: 암호가 헤더 검사를 통과하면 True, 아니면 False.
    """
    fp = zf.fp  # zip 파일의 실제 파일 포인터

    # zip 로컬 헤더 30바이트 읽기
    fp.seek(zinfo.header_offset)
    fheader = fp.read(30)

    # 파일명 길이와 추가 필드 길이를 little-endian 2바이트 정수로 파싱
    fname_len = struct.unpack_from('<H', fheader, 26)[0]
    extra_len = struct.unpack_from('<H', fheader, 28)[0]

    # 암호화 헤더 시작 위치로 이동 후 12바이트 읽기
    fp.seek(zinfo.header_offset + 30 + fname_len + extra_len)
    enc_header = fp.read(12)

    # zipfile 내부 ZipCrypto 복호화기로 헤더 복호화
    # _ZipDecrypter(pwd_bytes): 키 초기화 후 1바이트씩 복호화하는 callable 반환
    decrypter = zipfile._ZipDecrypter(pwd_bytes)
    decrypted = bytes(decrypter(b) for b in enc_header)

    # CRC-32 상위 1바이트와 복호화된 헤더 마지막 바이트 비교
    # (zinfo.CRC >> 24) & 0xff : CRC-32의 최상위 8비트 추출
    check_byte = (zinfo.CRC >> 24) & 0xff
    return decrypted[11] == check_byte


# ---------------------------------------------------------------------------
# 기본 과제: unlock_zip (단일 프로세스 브루트포스)
# ---------------------------------------------------------------------------

def unlock_zip(zip_path=ZIP_PATH, password_file=PASSWORD_FILE):
    """
    6자리 알파벳+숫자 조합으로 zip 파일 암호를 브루트포스로 해독한다.

    탐색 순서: 000000, 000001, ..., 00000z, 00001z, ..., zzzzzz
    (itertools.product가 사전식 순서로 자동 생성)

    Args:
        zip_path (str): 대상 zip 파일 경로.
        password_file (str): 발견된 암호를 저장할 파일 경로.

    Returns:
        str | None: 발견된 암호 문자열, 실패 시 None.
    """
    # 전체 경우의 수: 36^6 = 2,176,782,336
    total = len(CHARSET) ** PASSWORD_LENGTH

    start_ts = time.time()
    print(f'[*] 시작 시간  : {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'[*] 대상 파일  : {zip_path}')
    print(f'[*] 문자셋     : {CHARSET}  (길이={len(CHARSET)})')
    print(f'[*] 총 경우의수: {total:,}')
    print('-' * 60)

    try:
        # 파일 존재 여부 및 zip 유효성 검사 (FileNotFoundError, BadZipFile 대비)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zinfo = zf.infolist()[0]  # 암호 검증에 사용할 첫 번째 파일의 메타데이터
            count = 0  # 총 시도 횟수 카운터

            # itertools.product: 중첩 for문 없이 6자리 모든 조합을 사전식으로 생성
            # 예: product('01..z', repeat=6) → ('0','0','0','0','0','0'), ('0','0','0','0','0','1'), ...
            for combo in itertools.product(CHARSET, repeat=PASSWORD_LENGTH):
                password = ''.join(combo)  # 튜플 → 문자열 변환 ('a','b','c') → 'abc'
                count += 1

                # 과제 요구사항: 진행 상황 주기적 출력 (시작 시간·반복 횟수·경과 시간)
                if count % LOG_INTERVAL == 0:
                    elapsed = time.time() - start_ts
                    rate = count / elapsed if elapsed > 0 else 0
                    print(
                        f'  시도 {count:>13,} | '
                        f'{count / total * 100:6.3f}% | '
                        f'경과 {elapsed:8.1f}s | '
                        f'{rate:>12,.0f} pwd/s | '
                        f'현재: {password}'
                    )

                # [1단계] 헤더 검사: 12바이트만 복호화해 빠르게 필터링
                # → 약 255/256 확률로 여기서 탈락, 전체 압축 해제 생략
                if not _check_password_fast(zf, zinfo, password.encode()):
                    continue  # 헤더 불일치 → 즉시 다음 조합으로

                # [2단계] 전체 파일 복호화: 헤더 통과 시 오탐(false positive) 제거
                # 약 1/256 확률로 헤더를 통과한 틀린 암호를 최종 걸러냄
                try:
                    zf.read(zinfo.filename, pwd=password.encode())
                    # read() 성공 = 암호 일치 확정
                    elapsed = time.time() - start_ts
                    print(f'\n[+] 암호 발견    : {password}')
                    print(f'[+] 총 시도 횟수 : {count:,}')
                    print(f'[+] 소요 시간    : {elapsed:.3f}s')
                    _save_password(password, password_file)
                    return password

                except (RuntimeError, zlib.error, zipfile.BadZipFile):
                    # RuntimeError   : Python 3.12 이하에서 틀린 암호 시 발생
                    # zlib.error     : Python 3.13+에서 추가로 발생
                    # zipfile.BadZipFile: Python 3.14에서 추가로 발생
                    # → 모두 "틀린 암호"를 의미하므로 다음 시도로 계속
                    pass

    except FileNotFoundError:
        # zip 파일 자체가 없는 경우
        print(f'[-] 파일을 찾을 수 없습니다: {zip_path}')
        return None

    elapsed = time.time() - start_ts
    print(f'\n[-] 암호를 찾지 못했습니다. '
          f'시도: {count:,}회, 경과: {elapsed:.2f}s')
    return None


# ---------------------------------------------------------------------------
# 보너스 과제: unlock_zip_fast (멀티프로세싱 + 헤더 검사)
# ---------------------------------------------------------------------------

def _worker(first_chars, zip_path, result_queue):
    """
    지정된 첫 번째 문자 목록으로 시작하는 조합만 탐색하는 워커 프로세스.

    [분할 방식]
      CHARSET 첫 번째 문자(36개)를 코어 수(N)로 나누어 각 프로세스에 할당.
      예) 4코어: 프로세스0 → '0','a','i','q',...  프로세스1 → '1','b','j','r',...
      나머지 5자리는 각 프로세스가 독립적으로 완전 탐색.

    Args:
        first_chars (list[str]): 이 워커가 담당할 첫 번째 문자 목록.
        zip_path (str): 대상 zip 파일 경로.
        result_queue (multiprocessing.Queue): 발견된 암호를 메인 프로세스에 전달할 큐.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zinfo = zf.infolist()[0]
            for first in first_chars:
                # 나머지 5자리(PASSWORD_LENGTH - 1)의 모든 조합 탐색
                for tail in itertools.product(CHARSET, repeat=PASSWORD_LENGTH - 1):
                    password = first + ''.join(tail)
                    pwd_bytes = password.encode()

                    # [1단계] 헤더 빠른 검사
                    if not _check_password_fast(zf, zinfo, pwd_bytes):
                        continue

                    # [2단계] 전체 파일로 최종 확인
                    try:
                        zf.read(zinfo.filename, pwd=pwd_bytes)
                        # 암호 발견 → 큐에 넣고 즉시 종료
                        result_queue.put(password)
                        return
                    except (RuntimeError, zlib.error, zipfile.BadZipFile):
                        pass  # 오탐 → 다음 시도
    except FileNotFoundError:
        pass  # 워커에서는 조용히 종료 (메인에서 이미 검증됨)


def unlock_zip_fast(zip_path=ZIP_PATH, password_file=PASSWORD_FILE):
    """
    멀티프로세싱 + ZipCrypto 헤더 검사를 결합한 고속 브루트포스 해독기. (보너스 과제)

    [속도 개선 원리]
      1. ZipCrypto 헤더(12바이트)만 검사 → 전체 압축 해제 횟수 1/256로 감소
      2. 탐색 공간을 CPU 코어 수로 분할하여 병렬 탐색
      → 단일 프로세스 기본 방식 대비 약 (코어 수 × 10~30)배 빠름

    [multiprocessing을 쓰는 이유]
      Python의 GIL(Global Interpreter Lock)로 인해 threading은 CPU 연산을
      진짜 병렬로 실행하지 못함. multiprocessing은 별도 프로세스를 생성하여
      GIL의 제약 없이 각 CPU 코어를 완전히 활용할 수 있음.

    [프로세스 간 통신]
      multiprocessing.Queue를 통해 워커 프로세스 → 메인 프로세스로 결과 전달.
      하나의 프로세스가 암호를 찾으면 나머지 프로세스는 terminate()로 즉시 종료.

    Args:
        zip_path (str): 대상 zip 파일 경로.
        password_file (str): 발견된 암호를 저장할 파일 경로.

    Returns:
        str | None: 발견된 암호 문자열, 실패 시 None.
    """
    cpu_count = multiprocessing.cpu_count()

    # CHARSET을 코어 수만큼 인터리브 방식으로 분할
    # 예) CHARSET='0123...z', 4코어 →
    #   chunks[0]: ['0','4','8',...,'a','e','i',...]
    #   chunks[1]: ['1','5','9',...,'b','f','j',...]
    # → 각 프로세스가 탐색 공간의 앞뒤를 고루 담당해 균등 부하 분산
    chunks = [list(CHARSET[i::cpu_count]) for i in range(cpu_count)]

    start_ts = time.time()
    print(f'[FAST] 시작 시간  : {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'[FAST] CPU 코어   : {cpu_count}개')
    print(f'[FAST] 탐색 분할  : 첫 번째 문자 {len(CHARSET)}종 → {cpu_count}개 프로세스')
    print('-' * 60)

    result_queue = multiprocessing.Queue()
    processes = []

    # 각 코어에 워커 프로세스 생성 및 시작
    for chunk in chunks:
        if not chunk:
            continue
        p = multiprocessing.Process(
            target=_worker,
            args=(chunk, zip_path, result_queue)
        )
        p.start()
        processes.append(p)

    password = None
    try:
        # 결과 대기: 0.1초마다 큐를 확인하고 암호가 들어오면 루프 탈출
        while any(p.is_alive() for p in processes):
            if not result_queue.empty():
                password = result_queue.get()
                break
            time.sleep(0.1)

        # 레이스 컨디션 대비: 루프 종료 후에도 큐에 남은 결과 확인
        if password is None and not result_queue.empty():
            password = result_queue.get()

    finally:
        # 암호 발견 여부와 무관하게 모든 워커 프로세스 정리
        # terminate(): 강제 종료 / join(): 프로세스 완전 소멸 대기
        for p in processes:
            p.terminate()
            p.join()

    elapsed = time.time() - start_ts

    if password:
        print(f'[FAST] 암호 발견    : {password}')
        print(f'[FAST] 소요 시간    : {elapsed:.3f}s')
        _save_password(password, password_file)
    else:
        print(f'[FAST] 암호를 찾지 못했습니다. 경과: {elapsed:.2f}s')

    return password


# ---------------------------------------------------------------------------
# 공통 유틸리티
# ---------------------------------------------------------------------------

def _save_password(password, password_file):
    """
    발견된 암호를 텍스트 파일로 저장한다.

    OSError(권한 없음, 디스크 꽉 참 등) 발생 시 예외처리하여
    프로그램이 비정상 종료되지 않도록 보호한다.

    Args:
        password (str): 저장할 암호 문자열.
        password_file (str): 저장 경로.
    """
    try:
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(password)
        print(f'[+] 암호 저장    : {password_file}')
    except OSError as e:
        print(f'[-] 저장 실패    : {e}')


# ---------------------------------------------------------------------------
# 엔트리포인트
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # 보너스(빠른 버전) 먼저 실행
    # multiprocessing은 __main__ 가드 없이 실행하면 Windows에서
    # 자식 프로세스가 이 파일을 다시 import하면서 무한 프로세스 생성 오류 발생
    # → 반드시 if __name__ == '__main__': 안에서 실행해야 함
    print('=' * 60)
    print('  [보너스] 멀티프로세싱 + 헤더 검사 (빠른 버전)')
    print('=' * 60)
    result = unlock_zip_fast()

    # fast 버전 실패 시 단일 프로세스 기본 버전으로 폴백
    if result is None:
        print()
        print('=' * 60)
        print('  [기본] 단일 프로세스 브루트포스')
        print('=' * 60)
        unlock_zip()