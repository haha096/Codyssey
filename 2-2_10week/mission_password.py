import os

# 현재 파이썬 파일 위치로 작업 디렉토리 설정
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =============================================
# [수행과제 1] password.txt 파일을 읽어온다
# =============================================
try:
    with open("password.txt", "r") as f:
        password_text = f.read().strip()
    print("📄 암호문:", password_text)
    print()

except FileNotFoundError:
    print("❌ 오류: password.txt 파일을 찾을 수 없습니다.")
    exit()
except PermissionError:
    print("❌ 오류: password.txt 파일을 읽을 권한이 없습니다.")
    exit()
except Exception as e:
    print(f"❌ 파일 읽기 중 오류 발생: {e}")
    exit()


# =============================================
# [보너스 과제] 텍스트 사전 정의
# 암호문 속에서 이 단어 중 하나라도 발견되면 정답으로 판단
# =============================================
WORD_DICTIONARY = [
    "mars", "love", "earth", "space", "rocket",
    "base", "door", "open", "password", "key",
    "the", "is", "are", "have", "this"
]


# =============================================
# [보너스 과제] 사전 검사 함수
# =============================================
def check_dictionary(text):
    # [보너스 과제] 대소문자 구분 없이 비교하기 위해 소문자로 통일
    text_lower = text.lower()

    # [보너스 과제] 사전의 단어를 하나씩 꺼내어 해독 결과에 포함되어 있는지 확인
    for word in WORD_DICTIONARY:
        if word in text_lower:
            # [보너스 과제] 발견된 단어를 반환 → 호출한 곳에서 break 여부 결정
            return word

    # [보너스 과제] 사전 단어가 하나도 없으면 None 반환 → 반복 계속
    return None


# =============================================
# [수행과제 2] caesar_cipher_decode() 라는 이름으로 함수를 정의한다
# =============================================
def caesar_cipher_decode(target_text):
    # [수행과제 3] 풀어야 하는 문자열을 파라메터로 추가한다. 파라메터 이름은 target_text

    result_shift = None
    result_text = None

    # [수행과제 4] 자리수는 알파벳 수(26개)만큼 반복한다
    # → shift를 1부터 25까지 반복하여 자리수에 따라 암호표가 바뀌게 한다
    for shift in range(1, 26):

        decoded_text = ""

        for char in target_text:

            # [수행과제 4] 알파벳인 경우에만 암호표 변환을 적용한다
            if char.isalpha():

                # [수행과제 4] 대문자는 'A'(65), 소문자는 'a'(97)를 기준점으로 잡는다
                # → 기준점을 빼면 A=0, B=1 ... Z=25 의 숫자로 변환된다
                base = ord('A') if char.isupper() else ord('a')

                # [수행과제 4] 복호화 공식: 현재 문자에서 shift만큼 역방향으로 이동
                # → % 26 을 사용하여 Z를 넘어가면 A로 순환되게 한다
                # → 다시 chr()로 문자로 변환하여 decoded_text에 추가한다
                decoded_char = chr((ord(char) - base - shift) % 26 + base)
                decoded_text += decoded_char

            else:
                # [수행과제 4] 알파벳이 아닌 문자(공백, 숫자 등)는 변환 없이 그대로 유지한다
                decoded_text += char

        # [수행과제 5] 자리수(shift)에 따라 해독된 결과를 출력한다
        # [보너스 과제] 출력 전에 사전 단어 포함 여부를 먼저 검사한다
        found_word = check_dictionary(decoded_text)

        if found_word:
            # [수행과제 5] 사전 단어가 발견된 shift의 결과를 출력한다
            print(f"[shift {shift:2d}] {decoded_text}  ✅ 사전 단어 발견: '{found_word}'")
            result_shift = shift
            result_text = decoded_text

            # [보너스 과제] 사전 단어가 발견되는 순간 반복을 즉시 멈춘다
            break

        else:
            # [수행과제 5] 사전 단어가 없으면 결과를 출력하고 다음 shift로 계속 진행한다
            print(f"[shift {shift:2d}] {decoded_text}")

    # [수행과제 6] 몇 번째 자리수로 해독되었는지 반환한다
    return result_shift, result_text


# =============================================
# [수행과제 6] 함수를 실행하여 암호가 해독되는 자리수를 찾아낸다
# =============================================
print("=" * 60)
detected_shift, detected_text = caesar_cipher_decode(password_text)
print("=" * 60)
print()

if detected_text is None:
    print("⚠️  사전에서 일치하는 단어를 찾지 못했습니다.")
    print("💡 WORD_DICTIONARY에 단어를 추가해보세요.")

else:
    print(f"🔍 암호 해독 성공! shift: {detected_shift}번")
    print(f"🔓 해독 결과: {detected_text}")

    # [수행과제 6] 해독된 최종 결과를 result.txt 파일로 저장한다
    try:
        with open("result.txt", "w") as f:
            f.write(detected_text)
        print(f"💾 result.txt 저장 완료!")

    except PermissionError:
        print("❌ 오류: result.txt 파일을 저장할 권한이 없습니다.")
    except Exception as e:
        print(f"❌ 파일 저장 중 오류 발생: {e}")