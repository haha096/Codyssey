print('Hello Mars')

# -----------------------------------------
# 미션 컴퓨터 에러 사항 확인하기 (r모드 활용)
# -----------------------------------------

# f = open('C:/Users/Administrator/Desktop/Codyssey_1-1/mission_computer_main.log')
file_path = 'C:/Users/Administrator/Desktop/Codyssey_code/1-1_2week/mission_computer_main.log'
try:
    # with open('mission_computer_main.log') as f:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
        print(data)
except FileNotFoundError:
    print(f"오류: {f} 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")


# -----------------------------------------
# 분석보고서 파일 생성 및 쓰기 (w모드 활용)
# -----------------------------------------


analysis_report_content = '''
# 보고서 내용

## 개요 : 임무 중의 사고

* **사고원인** : 로그 데이터 분석 결과, 착륙 후의 산소 시스템 에러

* **사고일시**
**11:35:00:** 산소 탱크 불안정 증상 최초 포착 (Oxygen tank unstable)
* **11:40:00:** 산소 탱크 폭발 발생 (Oxygen tank explosion)
* **12:00:00:** 센터 및 임무 제어 시스템 전원 완전히 차단

## 결론
성공적인 착륙 이후 발생한 산소 탱크의 압력 조절 실패 또는 구조적 결함이 사고의 핵심 원인으로 파악됩니다.
'''

analysis_file_path = 'C:/Users/Administrator/Desktop/Codyssey_code/1-1_2week/log_analysis.md'

try:
    analysis_file = open(analysis_file_path, 'w', encoding='utf-8')
    analysis_file.write(analysis_report_content)
    print('성공적으로 보고서가 작성되었습니다')
    analysis_file.close()
except FileNotFoundError:
    print(f"오류 : 파일을 찾을 수 없습니다. 경로를 확인해주세요 {analysis_file_path}")
except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")




# -----------------------------------------
# 분석보고서 파일 읽기 (r모드 활용)
# -----------------------------------------

try:
    f = open(analysis_file_path,'r', encoding='utf-8')
    analysis_data = f.read()
    print(analysis_data)
    f.close()
except FileNotFoundError:
    print(f"오류: {analysis_file_path} 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")




# -------------------------------------
# 마크다운 명령어
# # 큰제목
# ## 중간제목
# ### 작은 제목

# *이탤릭*
# **볼드**
# ***이탤릭이면서 볼드***

# $수식모양$

# '''
# 코드블록
# '''
# -------------------------------------