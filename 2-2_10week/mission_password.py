import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =============================================
# [수행과제 1] password.txt 파일을 읽어온다
# =============================================
try:
    with open("password2.txt", "r") as f:
        password_text = f.read().strip()
    print("📄 암호문:", password_text)
    print()

except FileNotFoundError:
    print("❌ 오류: password2.txt 파일을 찾을 수 없습니다.")
    exit()
except PermissionError:
    print("❌ 오류: password2.txt 파일을 읽을 권한이 없습니다.")
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
# [2순위 자동 감지] 자주 쓰이는 영어 단어 목록
# 해독 결과에 이 단어들이 많이 포함될수록 진짜 문장일 확률이 높다
# =============================================
COMMON_ENGLISH_WORDS = [
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "is", "are", "was", "were", "be",
    "been", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "i", "you",
    "he", "she", "we", "they", "it", "this", "that", "my", "your",
    "his", "her", "our", "its", "not", "so", "if", "as", "up",
    "out", "about", "just", "like", "go", "get", "all", "from",
    "one", "two", "no", "yes", "me", "him", "us", "them", "what",
    "who", "how", "when", "where", "which", "there", "here", "now",
    "then", "than", "more", "some", "any", "only", "also", "very",
    "too", "well", "back", "still", "way", "even", "new", "want",
    "because", "come", "good", "know", "take", "see", "think", "look",
    "love", "mars", "earth", "space", "door", "open", "key", "time"
]


# =============================================
# [보너스 과제] 사전 검사 함수
# =============================================
def check_dictionary(text):
    # 대소문자 구분 없이 비교하기 위해 소문자로 통일
    text_lower = text.lower()

    # 사전의 단어를 하나씩 꺼내어 해독 결과에 포함되어 있는지 확인
    for word in WORD_DICTIONARY:
        if word in text_lower:
            return word

    # 사전 단어가 하나도 없으면 None 반환 → 반복 계속
    return None


# =============================================
# [2순위 자동 감지] 영어 단어 매칭 점수 계산 함수
# 해독 결과를 단어 단위로 쪼개서 COMMON_ENGLISH_WORDS에 몇 개나 있는지 카운트
# =============================================
def score_text(text):
    # [2순위 자동 감지] 해독 결과를 공백 기준으로 단어 단위로 분리한다
    words = text.lower().split()

    # [2순위 자동 감지] 분리된 단어들 중 자주 쓰이는 영어 단어 목록에 있는 것의 개수를 센다
    # → 개수가 많을수록 의미 있는 영어 문장일 확률이 높다
    count = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)

    return count


# =============================================
# [수행과제 2] caesar_cipher_decode() 라는 이름으로 함수를 정의한다
# =============================================
def caesar_cipher_decode(target_text):
    # [수행과제 3] 풀어야 하는 문자열을 파라메터로 추가한다. 파라메터 이름은 target_text

    # [2순위 자동 감지] 단어 매칭 점수가 가장 높은 결과를 담을 변수 초기화
    best_score = -1
    best_shift = None
    best_text = None

    # [보너스 과제] 사전 감지 결과를 담을 변수 초기화
    dict_shift = None
    dict_text = None
    dict_word = None

    # [수행과제 4] 자리수는 알파벳 수(26개)만큼 반복한다
    # → shift를 1부터 25까지 반복하여 자리수에 따라 암호표가 바뀌게 한다
    for shift in range(1, 26):

        decoded_text = ""

        for char in target_text:

            # [수행과제 4] 알파벳인 경우에만 암호표 변환을 적용한다
            if char.isalpha():

                # 컴퓨터는 문자를 숫자로 저장을 한다
                # 즉 카이사르 암호는 A = 0이라고 기억을 해야 편하지만
                # 컴퓨터는 A = 65라고 숫자를 기억하기 때문에 미리 사전에 문자의 숫자를 바꿔줌
                base = ord('A') if char.isupper() else ord('a')

                # 복호화 공식: 현재 문자에서 shift만큼 역방향으로 이동
                # → % 26 을 사용하여 Z를 넘어가면 A로 순환되게 한다
                # → 다시 chr()로 문자로 변환하여 decoded_text에 추가한다
                decoded_char = chr((ord(char) - base - shift) % 26 + base)
                decoded_text += decoded_char

            else:
                # [수행과제 4] 알파벳이 아닌 문자(공백, 숫자 등)는 변환 없이 그대로 유지한다
                decoded_text += char

        # [보너스 과제] 사전 단어 포함 여부를 먼저 검사한다 (1순위)
        found_word = check_dictionary(decoded_text)

        if found_word:
            # [수행과제 5] 사전 단어가 발견된 shift의 결과를 출력한다
            print(f"[shift {shift:2d}] {decoded_text}  ✅ 사전 단어 발견: '{found_word}'")
            dict_shift = shift
            dict_text = decoded_text
            dict_word = found_word

            # [보너스 과제] 사전 단어가 발견되는 순간 반복을 즉시 멈춘다
            break

        else:
            # [2순위 자동 감지] 이번 shift의 영어 단어 매칭 점수를 계산한다
            current_score = score_text(decoded_text)

            # [수행과제 5] 사전 단어가 없으면 점수와 함께 결과를 출력하고 다음 shift로 계속 진행한다
            print(f"[shift {shift:2d}] (단어 매칭: {current_score}개) {decoded_text}")

            # [2순위 자동 감지] 현재까지 가장 높은 점수의 shift를 기억해둔다
            if current_score > best_score:
                best_score = current_score
                best_shift = shift
                best_text = decoded_text

    # [수행과제 6] 1순위(사전 감지) 결과가 있으면 그것을 반환한다
    if dict_text is not None:
        print()
        print(f"🔍 [1순위 사전 감지] '{dict_word}' 단어 발견 → shift {dict_shift}번으로 해독 완료")
        return dict_shift, dict_text

    # [수행과제 6] 사전에서 못 찾은 경우 2순위(단어 매칭) 결과를 반환한다
    else:
        print()
        print(f"🔍 [2순위 단어 매칭] 사전 단어 없음 → 영어 단어 {best_score}개 매칭된 shift {best_shift}번으로 해독")
        return best_shift, best_text


# =============================================
# 함수를 실행하여 암호가 해독되는 자리수를 찾아낸다
# =============================================
print("=" * 60)
detected_shift, detected_text = caesar_cipher_decode(password_text)
print("=" * 60)
print()

print(f"🔓 최종 해독 결과 (shift {detected_shift}번): {detected_text}")

# =============================================
# 해독된 최종 결과를 result.txt 파일로 저장한다
# =============================================
try:
    with open("result2.txt", "w") as f:
        f.write(detected_text)
    print(f"💾 result2.txt 저장 완료!")

except PermissionError:
    print("오류: result2.txt 파일을 저장할 권한이 없습니다.")
except Exception as e:
    print(f"파일 저장 중 오류 발생: {e}")