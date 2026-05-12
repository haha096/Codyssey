"""
door_hacking.py

화성 기지 emergency storage 잠금 해제를 위한 zip 파일 브루트포스 암호 해독기.

암호 조건: 숫자(0-9) + 소문자 알파벳(a-z), 6자리, 특수문자 없음
           → 전체 경우의 수: 36^6 = 2,176,782,336 가지

알고리즘:
  [기본]  itertools.product로 모든 조합을 순서대로 생성하여 완전 탐색.
  [보너스] 탐색 공간을 CPU 코어 수만큼 분할하여 multiprocessing으로 병렬 탐색.
           zip 파일을 메모리에 올려 디스크 I/O 병목을 제거.

제약사항 준수:
  - zipfile(zip 처리), 그 외 모두 Python 표준 라이브러리만 사용
  - 파일 처리 전 구간 예외처리 (FileNotFoundError, OSError 등)
  - 경고 없이 실행되도록 Python 버전별 예외(RuntimeError, zlib.error, BadZipFile) 대응
  - PEP 8 스타일 가이드 준수
"""

import io
import itertools
import multiprocessing
import os
import string
import time
import zipfile
import zlib

# ---------------------------------------------------------------------------
# 전역 상수
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(_BASE_DIR, 'emergency_storage_key.zip')
PASSWORD_FILE = os.path.join(_BASE_DIR, 'password.txt')

# 암호 조건: 숫자 10개 + 소문자 26개 = 36가지 문자
CHARSET = string.digits + string.ascii_lowercase  # '0123456789abcdefghijklmnopqrstuvwxyz'

PASSWORD_LENGTH = 6
TOTAL = len(CHARSET) ** PASSWORD_LENGTH  # 36^6 = 2,176,782,336

# 워커가 공유 카운터를 업데이트할 간격
COUNTER_UPDATE_INTERVAL = 10_000

# 단일 프로세스 진행 상황 출력 간격
LOG_INTERVAL = 5_000_000


# ---------------------------------------------------------------------------
# 공통 유틸리티
# ---------------------------------------------------------------------------

def _try_password(zf, filename, pwd_bytes):
    """
    zip 파일에서 주어진 암호로 파일 읽기를 시도한다.

    Args:
        zf (zipfile.ZipFile): 열린 ZipFile 객체.
        filename (str): zip 안의 파일명.
        pwd_bytes (bytes): 시도할 암호 (bytes).

    Returns:
        bool: 암호 일치 시 True, 불일치 시 False.
    """
    try:
        zf.read(filename, pwd=pwd_bytes)
        return True
    except (RuntimeError, zlib.error, zipfile.BadZipFile):
        return False


def _save_password(password, password_file):
    """발견된 암호를 텍스트 파일로 저장한다."""
    try:
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(password)
        print(f'[+] 암호 저장    : {password_file}')
    except OSError as e:
        print(f'[-] 저장 실패    : {e}')


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
    start_ts = time.time()
    print(f'[*] 시작 시간  : {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'[*] 대상 파일  : {zip_path}')
    print(f'[*] 문자셋     : {CHARSET}  (길이={len(CHARSET)})')
    print(f'[*] 총 경우의수: {TOTAL:,}')
    print('-' * 60)

    try:
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
    except FileNotFoundError:
        print(f'[-] 파일을 찾을 수 없습니다: {zip_path}')
        return None

    # zip 파일을 메모리(BytesIO)에서 열기 → 디스크 I/O 없이 탐색
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf:
        filename = zf.namelist()[0]
        count = 0

        for combo in itertools.product(CHARSET, repeat=PASSWORD_LENGTH):
            password = ''.join(combo)
            count += 1

            if count % LOG_INTERVAL == 0:
                elapsed = time.time() - start_ts
                rate = count / elapsed if elapsed > 0 else 0
                print(
                    f'  시도 {count:>13,} | '
                    f'{count / TOTAL * 100:6.3f}% | '
                    f'경과 {elapsed:8.1f}s | '
                    f'{rate:>12,.0f} pwd/s | '
                    f'현재: {password}'
                )

            if _try_password(zf, filename, password.encode()):
                elapsed = time.time() - start_ts
                print(f'\n[+] 암호 발견    : {password}')
                print(f'[+] 총 시도 횟수 : {count:,}')
                print(f'[+] 소요 시간    : {elapsed:.3f}s')
                _save_password(password, password_file)
                return password

    elapsed = time.time() - start_ts
    print(f'\n[-] 암호를 찾지 못했습니다. '
          f'시도: {count:,}회, 경과: {elapsed:.2f}s')
    return None


# ---------------------------------------------------------------------------
# 보너스 과제: unlock_zip_fast (멀티프로세싱 + 메모리 탑재)
# ---------------------------------------------------------------------------

def _worker(first_chars, zip_data, result_queue, counter, lock):
    """
    지정된 첫 번째 문자 목록으로 시작하는 조합만 탐색하는 워커 프로세스.

    [핵심] zip_data는 zip 파일의 bytes 데이터.
    io.BytesIO로 메모리에서 직접 열기 때문에 디스크 접근이 전혀 없다.
    20개 프로세스가 동시에 같은 파일을 디스크에서 읽을 때 생기는
    I/O 병목이 사라져 CPU를 온전히 암호 연산에만 사용할 수 있다.

    Args:
        first_chars (list[str])         : 이 워커가 담당할 첫 번째 문자 목록.
        zip_data (bytes)                : 메모리에 올린 zip 파일 전체 데이터.
        result_queue (Queue)            : 발견된 암호를 메인 프로세스에 전달할 큐.
        counter (multiprocessing.Value) : 전체 워커가 공유하는 시도 횟수 카운터.
        lock (multiprocessing.Lock)     : counter 동시 접근을 막는 잠금 객체.
    """
    # io.BytesIO: bytes 데이터를 파일처럼 다룰 수 있게 해주는 메모리 버퍼
    # → 디스크 I/O 없이 zip을 읽을 수 있음
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf:
        filename = zf.namelist()[0]
        local_count = 0  # 로컬 카운터 (공유 카운터 업데이트 주기 계산용)

        for first in first_chars:
            for tail in itertools.product(CHARSET, repeat=PASSWORD_LENGTH - 1):
                password = first + ''.join(tail)
                local_count += 1

                # COUNTER_UPDATE_INTERVAL마다 공유 카운터에 반영
                # lock으로 보호하여 동시 쓰기 충돌 방지
                if local_count % COUNTER_UPDATE_INTERVAL == 0:
                    with lock:
                        counter.value += COUNTER_UPDATE_INTERVAL

                # 방금 만든 비밀번호를 바이트(bytes) 형태로 변환해 압축 해제를 시도합니다. 풀린다면 반복문을 멈추고 결과를 출력합니다.
                if _try_password(zf, filename, password.encode()):
                    with lock:
                        counter.value += local_count % COUNTER_UPDATE_INTERVAL
                    result_queue.put(password)
                    return


def unlock_zip_fast(zip_path=ZIP_PATH, password_file=PASSWORD_FILE):
    """
    멀티프로세싱으로 탐색 공간을 CPU 코어 수만큼 분할하여 병렬 탐색한다. (보너스 과제)

    [속도 개선 원리]
      1. zip 파일을 메모리(bytes)에 올려 모든 워커가 디스크 접근 없이 탐색.
         → 20개 프로세스가 동시에 같은 파일을 읽는 I/O 병목 완전 제거.
      2. 탐색 공간을 CPU 코어 수로 분할하여 진짜 병렬 실행.
         → 이론상 코어 수배 빠름.

    [프로세스 간 통신]
      - result_queue : 워커 → 메인으로 발견된 암호 전달.
      - counter + lock: 워커들이 공유하는 시도 횟수. 메인이 1초마다 읽어 진행률 출력.

    Args:
        zip_path (str): 대상 zip 파일 경로.
        password_file (str): 발견된 암호를 저장할 파일 경로.

    Returns:
        str | None: 발견된 암호 문자열, 실패 시 None.
    """
    # zip 파일 전체를 메모리에 적재 (이후 디스크 접근 없음)
    try:
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
    except FileNotFoundError:
        print(f'[-] 파일을 찾을 수 없습니다: {zip_path}')
        return None

    cpu_count = multiprocessing.cpu_count()

    # CHARSET을 코어 수만큼 인터리브 방식으로 분할
    # 인터리브: 숫자/알파벳이 모든 프로세스에 고루 분배되어 균등 부하 분산
    chunks = [list(CHARSET[i::cpu_count]) for i in range(cpu_count)]

    # 공유 카운터: 모든 워커의 총 시도 횟수를 누적
    counter = multiprocessing.Value('q', 0)
    lock = multiprocessing.Lock()
    result_queue = multiprocessing.Queue()
    processes = []

    start_ts = time.time()
    print(f'[FAST] 시작 시간  : {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'[FAST] CPU 코어   : {cpu_count}개')
    print(f'[FAST] 탐색 분할  : 첫 번째 문자 {len(CHARSET)}종 → {cpu_count}개 프로세스')
    print(f'[FAST] 총 경우의수: {TOTAL:,}')
    print('-' * 60)

    for chunk in chunks:
        if not chunk:
            continue
        p = multiprocessing.Process(
            target=_worker,
            args=(chunk, zip_data, result_queue, counter, lock)
        )
        p.start()
        processes.append(p)

    password = None
    prev_count = 0
    prev_ts = start_ts

    try:
        while any(p.is_alive() for p in processes):
            time.sleep(120)

            with lock:
                current_count = counter.value

            now = time.time()
            elapsed = now - start_ts
            interval = now - prev_ts
            rate = (current_count - prev_count) / interval if interval > 0 else 0
            remaining = TOTAL - current_count
            eta = remaining / rate if rate > 0 else 0
            eta_str = time.strftime('%H:%M:%S', time.gmtime(eta))

            print(
                f'  총시도 {current_count:>13,} | '
                f'{current_count / TOTAL * 100:6.3f}% | '
                f'경과 {elapsed:7.1f}s | '
                f'{rate:>10,.0f} pwd/s | '
                f'예상잔여 {eta_str}'
            )

            prev_count = current_count
            prev_ts = now

            if not result_queue.empty():
                password = result_queue.get()
                break

        if password is None and not result_queue.empty():
            password = result_queue.get()

    finally:
        for p in processes:
            p.terminate()
            p.join()

    elapsed = time.time() - start_ts

    if password:
        print(f'\n[FAST] 암호 발견    : {password}')
        print(f'[FAST] 총 소요 시간 : {elapsed:.3f}s')
        _save_password(password, password_file)
    else:
        print(f'[FAST] 암호를 찾지 못했습니다. 경과: {elapsed:.2f}s')

    return password


# ---------------------------------------------------------------------------
# 엔트리포인트
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print('=' * 60)
    print('  [보너스] 멀티프로세싱 병렬 브루트포스 (빠른 버전)')
    print('=' * 60)
    result = unlock_zip_fast()

    # if result is None:
    #     print()
    #     print('=' * 60)
    #     print('  [기본] 단일 프로세스 브루트포스')
    #     print('=' * 60)
    #     unlock_zip()