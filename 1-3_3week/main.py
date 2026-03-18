import csv
import os
import pickle

# os모듈의 사용처
# -> 파일이나 디렉토리 조작이 가능
# 파일의 목록이나 path를 얻을 수 있음
# 새로운 파일 혹은 디렉토리를 작성하는 것도 가능


# -----------------------------------------------
# Mars_Base_Inventory_List.csv 파일을 읽어 출력
# -----------------------------------------------

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

mars_list = []

try :
    with open(csv_file_path, 'r', encoding='utf-8') as c_file_path:
        reader = csv.reader(c_file_path)
        # read = csv.read(c_file_path)
        # -> 이때 csv파일을 read로 읽어올 때는 AttributeError라는 에러가 생김
        print(reader)
        # <_csv.reader object at 0x02351WCEW7GW254>
        mars_list = list(reader)
except FileNotFoundError :
    print("파일 경로 혹은 이름이 잘못되었습니다")

except Exception as e :
    print(f"{e} -> 다른 문제가 생겼습니다")

# print(mars_list)


# -----------------------------------------------
# 배열 내용을 인화성 높은 순으로 정렬
# 인화성 지수가 0.7이상 되는 목록을 뽑아 별도로 출력
# -----------------------------------------------

data_list = mars_list[1:]

def get_flammability(x):
    return float(x[4])

flammability_sorted2 = sorted(data_list, key=get_flammability, reverse=True)

flammability_sorted = sorted(data_list, key=lambda x : float(x[4]), reverse=True)

# 인화성물질이 높은 순으로 정렬된 리스트
# print(flammability_sorted)

danger_flammability_list = []

for i in flammability_sorted :
    if(float(i[4]) >= 0.7) :
        danger_flammability_list.append(i)

# print(danger_flammability_list)

# -----------------------------------------------
# 인화성 지수가 0.7 이상되는 목록을 csv 포멧 & 저장
# Mars_Base_Inventory_danger.csv로 저장한다
# -----------------------------------------------

danger_flammability_csv_file_path = os.path.join(current_dir, 'Mars_Base_Inventory_danger.csv')

try :
    # danger_flammability_file = open(danger_flammability_csv_file_path, 'w', encoding='utf-8', newline='')

    # writer = csv.writer(danger_flammability_file)
    # writer.writerows(danger_flammability_list)

    # danger_flammability_file.close()

    with open(danger_flammability_csv_file_path, 'w', encoding='utf-8', newline='') as danger_flammability_file:
        writer = csv.writer(danger_flammability_file)
        writer.writerows(danger_flammability_list)

except FileNotFoundError :
    print("파일 경로 혹은 이름이 잘못되었습니다")

except Exception as e :
    print(f"{e} -> 다른 문제가 생겼습니다")



# -----------------------------------------------
# 보너스 과제 1
# 인화성 순서대로 정렬된 내용을 이진 파일형태로 저장
# 파일이름은 Mars_Base_Inventory_List.bin
# -----------------------------------------------

danger_flammability_binfile_path = os.path.join(current_dir, 'Mars_Base_Inventory_List.bin')

try :
    with open(danger_flammability_binfile_path, 'wb') as danger_flammability_binfile:
        pickle.dump(danger_flammability_list, danger_flammability_binfile)

except FileNotFoundError :
    print("파일 경로 혹은 이름이 잘못되었습니다")

except Exception as e :
    print(f"{e} -> 다른 문제가 생겼습니다")


# -----------------------------------------------
# 보너스 과제 2
# 저장된 Mars_Base_Inventory_List.bin를 읽어 화면에 출력
# -----------------------------------------------

try :
    with open(danger_flammability_binfile_path, 'rb') as danger_flammability_binfile:
        danger_flammability_binfile_data = pickle.load(danger_flammability_binfile)
        print(danger_flammability_binfile_data)

except FileNotFoundError :
    print("파일 경로 혹은 이름이 잘못되었습니다")

except Exception as e :
    print(f"{e} -> 다른 문제가 생겼습니다")