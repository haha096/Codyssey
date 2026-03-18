import csv
import os

# os모듈의 사용처
# -> 파일이나 디렉토리 조작이 가능
# 파일의 목록이나 path를 얻을 수 있음
# 새로운 파일 혹은 디렉토리를 작성하는 것도 가능


# -----------------------------------------
# Mars_Base_Inventory_List.csv 파일을 읽어 출력
# -----------------------------------------

# os.path는 폴더명이나 파일명의 존재유무를 파악할 수 있는 모듈
# os.path.abspath -> 파일의 절대경로를 찾아주는 모듈
# __file__ -> 현재 파일의 이름(main.py)
# os.path.dirname -> 경로의 디렉터리명을 반환(1-3_3week 디렉터리명 반환)
# os.path.join -> 경로와 파일명을 결합하고 싶을 때 사용하는 모듈
#              -> 해당 파일이 위치한 절대경로를 불러와 파일명을 결합할 수 있음

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
csv_file_path = os.path.join(current_dir, 'Mars_Base_Inventory_List.csv')
# -> 지금 1-3_3week의 디렉터리의 파일경로와 Mars_Base_Inventory_List.csv파일을 결합해 csv파일의 절대경로를 얻음


# csv파일을 읽어서 출력을 하려면 reader라는 전용함수를 사용해 깔끔하게 리스트 형태로 뽑아내야 함

with open(csv_file_path, 'r', encoding='utf-8') as c_file_path:
    reader = csv.reader(c_file_path)
    # read = csv.read(c_file_path)
    # -> 이때 csv파일을 read로 읽어올 때는 AttributeError라는 에러가 생김
    print(reader)
    # <_csv.reader object at 0x02351WCEW7GW254>
    mars_list = list(reader)

print(mars_list)

